from dotenv import load_dotenv

from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory

import os

#################################

from castle.client import Client
from castle.errors import CastleError, WebhookVerificationError
from castle.webhooks.verify import WebhooksVerify

from datetime import datetime, timezone

#################################

import castle_config  # noqa: F401  (importing configures the Castle SDK)

from demo_config import demos, demo_list, valid_urls

#################################

load_dotenv()

# Demo fixture defaults. Only castle_pk and castle_api_secret need to be set in
# .env; the simulated "valid user" the demo logs in falls back to these values.
DEMO_DEFAULTS = {
    "location": "localhost",
    "valid_username": "clark.kent@dailyplanet.com",
    "valid_name": "Clark Kent",
    "valid_user_id": "00000000",
    "valid_password": "1234",
    "invalid_password": "qwerty",
    "webhook_url": "https://webhook.site",
}
for _key, _value in DEMO_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

app = Flask(__name__)

# Serve the Castle browser SDK straight from the npm install (node_modules)
# instead of vendoring it into the repo.
CASTLE_JS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'node_modules', '@castleio', 'castle-js', 'dist'
)


@app.route('/vendor/castle-js/<path:filename>')
def castle_js(filename):
    return send_from_directory(CASTLE_JS_DIR, filename)

#################################
# Helpers
#################################

# default params to be rendered with every page
def get_default_params():

    default_params = {
        "castle_pk": os.getenv('castle_pk'),
        "location": os.getenv('location'),
        "demo_list": demo_list,
        "username": os.getenv("valid_username"),
        "invalid_password": os.getenv("invalid_password"),
        "valid_password": os.getenv("valid_password"),
        "valid_username": os.getenv("valid_username"),
        "valid_name": os.getenv("valid_name") or "Clark Kent",
        "webhook_url": os.getenv("webhook_url")
    }

    return default_params


def castle_client():
    # The Lists, Privacy and Events APIs are account-level and do not need a
    # request context, so a bare client is enough.
    return Client({'context': {}})


# another default value
registered_at = '2020-02-23T22:28:55.387Z'

# In-memory store of the most recent webhooks received from Castle. A real app
# would persist these; a list is plenty for a localhost demo.
received_webhooks = []
webhook_seq = 0

#################################
# Page routes
#################################

@app.route('/')
def home():

    params = get_default_params()

    params["home"] = True

    return render_template('demo.html', **params)

@app.route('/<demo_name>')
def demo(demo_name):

    params = get_default_params()

    if demo_name not in valid_urls:

        return render_template('error.html', **params)

    ##########################################

    this_demo = demos[demo_name]

    for k, v in this_demo.items():

        params[k] = v

        params["demo_name"] = demo_name

        params[demo_name] = True

    template = demo_name + '.html'

    return render_template(template, **params)

#################################
# Filter (registration)
#################################

@app.route('/evaluate_signup', methods=['POST'])
def evaluate_signup():

    email = request.json["email"]
    request_token = request.json["request_token"]

    castle_type = "$registration"

    # A registration is evaluated before the account exists, so it is anonymous
    # activity sent to /filter with the form params (email/phone only). A brand-
    # new email is an attempt; an email that already belongs to a user is a
    # failed registration, resolved to that user via matching_user_id.
    if email == os.getenv("valid_username"):
        castle_status = "$failed"
        payload_to_castle = {
            'type': castle_type,
            'status': castle_status,
            'params': {'email': email},
            'matching_user_id': os.getenv("valid_user_id"),
            'request_token': request_token,
        }
    else:
        castle_status = "$attempted"
        payload_to_castle = {
            'type': castle_type,
            'status': castle_status,
            'params': {'email': email},
            'request_token': request_token,
        }

    castle = Client.from_request(request)
    verdict = castle.filter(payload_to_castle)

    return {
        "api_endpoint": "filter",
        "payload_to_castle": payload_to_castle,
        "result": verdict,
        "castle_type": castle_type,
        "castle_status": castle_status,
    }, 200, {'ContentType': 'application/json'}

#################################
# Filter -> Risk (login)
#################################

@app.route('/evaluate_login', methods=['POST'])
def evaluate_login():

    email = request.json["email"]
    password = request.json["password"]
    request_token = request.json["request_token"]

    castle_type = "$login"

    # A login reuses one request token across two calls: first Filter the attempt
    # while the visitor is still anonymous, then — on success — assess the
    # authenticated user with Risk. A failed attempt stays on Filter.
    castle = Client.from_request(request)

    def run_step(api_endpoint, castle_status, fields):
        payload_to_castle = {
            'type': castle_type,
            'status': castle_status,
            **fields,
            'request_token': request_token,
        }
        if api_endpoint == "risk":
            verdict = castle.risk(payload_to_castle)
        else:
            verdict = castle.filter(payload_to_castle)
        return {
            "api_endpoint": api_endpoint,
            "payload_to_castle": payload_to_castle,
            "result": verdict,
            "castle_type": castle_type,
            "castle_status": castle_status,
        }

    # Step 1 — always filter the attempt up front (anonymous -> params).
    steps = [run_step("filter", "$attempted", {'params': {'email': email}})]

    # Step 2 — the outcome, on the same request token.
    if email == os.getenv("valid_username") and password == os.getenv("valid_password"):
        steps.append(run_step("risk", "$succeeded", {
            'user': {
                'id': os.getenv("valid_user_id"),
                'email': email,
                'registered_at': registered_at,
            },
        }))
    else:
        fields = {'params': {'email': email}}
        # A known email with a wrong password resolves to the existing user.
        if email == os.getenv("valid_username"):
            fields['matching_user_id'] = os.getenv("valid_user_id")
        steps.append(run_step("filter", "$failed", fields))

    return {"steps": steps}, 200, {'ContentType': 'application/json'}

#################################
# Risk (profile update)
#################################

@app.route('/evaluate_profile_update', methods=['POST'])
def evaluate_profile_update():

    name = request.json.get("name")
    email = request.json.get("email") or os.getenv("valid_username")
    request_token = request.json["request_token"]

    castle_type = "$profile_update"
    castle_status = "$succeeded"

    payload_to_castle = {
        'type': castle_type,
        'status': castle_status,
        'user': {
            'id': os.getenv("valid_user_id"),
            'email': email,
            'name': name,
            'registered_at': registered_at,
        },
        'request_token': request_token,
    }

    # A profile change is a sensitive action, so evaluate it with /risk.
    castle = Client.from_request(request)
    verdict = castle.risk(payload_to_castle)

    return {
        "api_endpoint": "risk",
        "payload_to_castle": payload_to_castle,
        "result": verdict,
        "castle_type": castle_type,
        "castle_status": castle_status,
    }, 200, {'ContentType': 'application/json'}

#################################
# Log (password reset)
#################################

@app.route('/evaluate_new_password', methods=['POST'])
def evaluate_new_password():

    print(request.json)

    password = request.json["password"]
    request_token = request.json["request_token"]

    # A new password that differs from the current one is a successful reset.
    if password == os.getenv("valid_password"):
        castle_status = "$failed"
    else:
        castle_status = "$succeeded"

    castle_type = "$password_reset"

    payload_to_castle = {
        'type': castle_type,
        'status': castle_status,
        'user': {
          'id': os.getenv("valid_user_id"),
          'email': os.getenv("valid_username"),
          'registered_at': registered_at
        },
        'request_token': request_token
    }

    # $password_reset is a good fit for the non-blocking log endpoint: we want
    # to record the event without waiting on a verdict.
    castle = Client.from_request(request)
    castle.log(payload_to_castle)

    r = {
        "api_endpoint": "log",
        "payload_to_castle": payload_to_castle,
        'type': castle_type,
        'status': castle_status,
    }

    return r, 200, {'ContentType':'application/json'}

#################################
# Log (logout)
#################################

@app.route('/evaluate_logout', methods=['POST'])
def evaluate_logout():

    request_token = request.json["request_token"]

    castle_type = "$logout"
    castle_status = "$succeeded"

    payload_to_castle = {
        'type': castle_type,
        'status': castle_status,
        'user': {
            'id': os.getenv("valid_user_id"),
            'email': os.getenv("valid_username"),
        },
        'request_token': request_token,
    }

    # Logout is recorded with the non-blocking log endpoint as well.
    castle = Client.from_request(request)
    castle.log(payload_to_castle)

    return {
        "api_endpoint": "log",
        "payload_to_castle": payload_to_castle,
        "castle_type": castle_type,
        "castle_status": castle_status,
    }, 200, {'ContentType': 'application/json'}

#################################
# Lists API
#################################

@app.route('/create_list', methods=['POST'])
def create_list():

    print(request.json)

    payload = {
        'name': request.json.get('name') or 'demo-blocklist',
        'color': request.json.get('color') or '$red',
        'primary_field': request.json.get('primary_field') or 'user.email',
    }

    castle = castle_client()

    try:
        created = castle.create_list(payload)
        all_lists = castle.get_all_lists()
        result = {"created": created, "all_lists": all_lists}
    except CastleError as error:
        result = {"error": str(error)}

    return {
        "api_endpoint": "lists",
        "payload_to_castle": payload,
        "result": result,
    }, 200, {'ContentType': 'application/json'}

#################################
# Privacy API
#################################

@app.route('/privacy_user_data', methods=['POST'])
def privacy_user_data():

    print(request.json)

    action = request.json.get("action", "request")

    payload = {
        'identifier': request.json.get('identifier') or os.getenv("valid_username"),
        'identifier_type': request.json.get('identifier_type') or '$email',
    }

    castle = castle_client()

    try:
        if action == "delete":
            api_endpoint = "privacy (delete)"
            result = castle.delete_user_data(payload)
        else:
            api_endpoint = "privacy (request)"
            result = castle.request_user_data(payload)
    except CastleError as error:
        api_endpoint = "privacy"
        result = {"error": str(error)}

    return {
        "api_endpoint": api_endpoint,
        "payload_to_castle": payload,
        "result": result,
    }, 200, {'ContentType': 'application/json'}

#################################
# Webhooks
#################################

@app.route('/webhooks')
def webhooks():

    params = get_default_params()

    params.update(demos["webhooks"])
    params["demo_name"] = "webhooks"
    params["webhooks"] = True

    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    params["webhook_endpoint"] = f"{proto}://{request.host}/webhooks/castle"
    params["webhooks_received"] = received_webhooks

    return render_template('webhooks.html', **params)


@app.route('/webhooks/castle', methods=['POST'])
def receive_webhook():

    # Verify the signature against the raw body; anything that fails gets a 404
    # so we don't reveal the endpoint to unauthenticated callers.
    try:
        WebhooksVerify.call(request)
    except WebhookVerificationError:
        return render_template('error.html', **get_default_params()), 404

    global webhook_seq
    webhook_seq += 1

    received_webhooks.insert(0, {
        "id": webhook_seq,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "body": request.get_json(silent=True),
    })
    del received_webhooks[50:]

    return '', 204


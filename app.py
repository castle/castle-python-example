from dotenv import load_dotenv

from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory

import os

#################################

from castle.client import Client
from castle.errors import CastleError

#################################

import castle_config  # noqa: F401  (importing configures the Castle SDK)

from demo_config import demos, demo_list, valid_urls

#################################

load_dotenv()

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
# Risk / Filter (registration)
#################################

@app.route('/evaluate_signup', methods=['POST'])
def evaluate_signup():

    name = request.json.get("name")
    email = request.json["email"]
    request_token = request.json["request_token"]

    castle_type = "$registration"

    # An email that's already taken (the known demo user) is a failed
    # registration and goes to /filter; a fresh sign-up is risk-assessed.
    if email == os.getenv("valid_username"):
        castle_status = "$failed"
        castle_api_endpoint = "filter"
    else:
        castle_status = "$succeeded"
        castle_api_endpoint = "risk"

    payload_to_castle = {
        'type': castle_type,
        'status': castle_status,
        'user': {
            'id': os.getenv("valid_user_id"),
            'email': email,
            'name': name,
        },
        'request_token': request_token,
    }

    castle = Client.from_request(request)

    if castle_api_endpoint == "risk":
        verdict = castle.risk(payload_to_castle)
    else:
        verdict = castle.filter(payload_to_castle)

    return {
        "api_endpoint": castle_api_endpoint,
        "payload_to_castle": payload_to_castle,
        "result": verdict,
        "castle_type": castle_type,
        "castle_status": castle_status,
    }, 200, {'ContentType': 'application/json'}

#################################
# Risk / Filter (login)
#################################

@app.route('/evaluate_login', methods=['POST'])
def evaluate_login():

    global registered_at

    print(request.json)

    email = request.json["email"]
    password = request.json["password"]
    request_token = request.json["request_token"]

    # check validity of username + password combo
    if email == os.getenv("valid_username"):

        user_id = os.getenv("valid_user_id")

        if password == os.getenv("valid_password"):
            castle_type = "$login"
            castle_status = "$succeeded"
            castle_api_endpoint = "risk"
        else:
            castle_type = "$login"
            castle_status = "$failed"
            castle_api_endpoint = "filter"
    else:
        castle_api_endpoint = "filter"
        castle_type = "$login"
        castle_status = "$failed"
        user_id = None
        registered_at = None

    payload_to_castle = {
        'type': castle_type,
        'status': castle_status,
        'user': {
          'id': user_id,
          'email': email
        },
        'request_token': request_token
    }

    if registered_at:
        payload_to_castle["user"]["registered_at"] = registered_at

    castle = Client.from_request(request)

    if castle_api_endpoint == "risk":
        verdict = castle.risk(payload_to_castle)

    elif castle_api_endpoint == "filter":
        verdict = castle.filter(payload_to_castle)

    print("verdict:")
    print(verdict)

    r = {
        "api_endpoint": castle_api_endpoint,
        "payload_to_castle": payload_to_castle,
        "result": verdict,
        "castle_type": castle_type,
        "castle_status": castle_status
    }

    return r, 200, {'ContentType':'application/json'}

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


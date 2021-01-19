from dotenv import load_dotenv

from flask import Flask
from flask import render_template
from flask import request

import base64
import json
import os
import requests

#################################

import castle
from castle.client import Client

#################################

import castle_config

from demo_config import demos, demo_list, valid_urls

#################################

load_dotenv()

app = Flask(__name__)

#################################
# Routes
#################################

# default params to be rendered with every page
def get_default_params():

    default_params = {
        "castle_app_id": os.getenv('castle_app_id'),
        "location": os.getenv('location'),
        "demo_list": demo_list,
        "username": os.getenv("valid_username"),
        "valid_password": os.getenv("valid_password"),
        "valid_username": os.getenv("valid_username"),
        "webhook_url": os.getenv("webhook_url")
    }

    return default_params

# another default value
registered_at = '2020-02-23T22:28:55.387Z'

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

@app.route('/evaluate_login', methods=['POST'])
def evaluate_login():

    global registered_at

    print(request.json)

    client_id = request.json["client_id"]
    email = request.json["email"]
    password = request.json["password"]

    # check validity of username + password combo
    if email == os.getenv("valid_username"):

        user_id = os.getenv("valid_user_id")

        if password == os.getenv("valid_password"):
            castle_event = "$login.succeeded"
            castle_api_endpoint = "authenticate"
        else:
            castle_api_endpoint = "track"
            castle_event = "$login.failed"
    else:
        castle_api_endpoint = "track"
        castle_event = "$login.failed"
        user_id = None
        registered_at = None

    payload_to_castle = {
        'event': castle_event,
        'user_id': user_id,
        'user_traits': {
            'email': email
        },
        'context': {
            'client_id': client_id
        }
    }

    if registered_at:
        payload_to_castle["user_traits"]["registered_at"] = registered_at

    castle = Client.from_request(request)

    if castle_api_endpoint == "authenticate":
        verdict = castle.authenticate(payload_to_castle)

    elif castle_api_endpoint == "track":
        verdict = castle.track(payload_to_castle)

    print("verdict:")
    print(verdict)

    r = {
        "api_endpoint": castle_api_endpoint,
        "payload_to_castle": payload_to_castle,
        "result": verdict,
        "castle_event": castle_event
    }

    if "device_token" in verdict:
        r["device_token"] = verdict["device_token"]

    if "action" in verdict:
        r["action"] = verdict["action"]

    return r, 200, {'ContentType':'application/json'}

@app.route('/evaluate_new_password', methods=['POST'])
def evaluate_new_password():

    print(request.json)

    client_id = request.json["client_id"]
    password = request.json["password"]

    # check validity of username + password combo
    if password == os.getenv("valid_password"):
        castle_event = "$password_reset.failed"
    else:
        castle_event = "$password_reset.succeeded"

    payload_to_castle = {
        'event': castle_event,
        'user_id': os.getenv("valid_user_id"),
        'user_traits': {
            'email': os.getenv("valid_username"),
            'registered_at': registered_at
        },
        'context': {
            'client_id': client_id
        }
    }

    castle = Client.from_request(request)

    r = {
        "api_endpoint": "track",
        "payload_to_castle": payload_to_castle,
        "castle_event": castle_event
    }

    return r, 200, {'ContentType':'application/json'}


@app.route('/get_device_info', methods=['POST'])
def get_device_info():

    print(request.json)

    url = "https://api.castle.io/v1/devices/"

    url += request.json["device_token"]

    message = ":" + os.getenv('castle_api_secret')

    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    authz_string = 'Basic ' + base64_bytes.decode('ascii')

    payload={}

    headers = {
      'Content-Type': 'application/json',
      'Authorization': authz_string
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

    r = {
        "api_endpoint": "devices",
        "device_info": response.json()
    }

    return r, 200, {'ContentType':'application/json'}

def get_authz_string():
    message = ":" + os.getenv('castle_api_secret')

    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    return 'Basic ' + base64_bytes.decode('ascii')

@app.route('/review_my_devices', methods=['POST'])
def review_my_devices():

    print(request.json)

    api_endpoint = "users/" + os.getenv("valid_user_id") + "/devices"

    url = "https://api.castle.io/v1/" + api_endpoint

    payload={}

    headers = {
      'Content-Type': 'application/json',
      'Authorization': get_authz_string()
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

    r = {
        "api_endpoint": api_endpoint, 
        "devices": response.json()
    }

    return r, 200, {'ContentType':'application/json'}

@app.route('/update_device', methods=['POST'])
def update_device():

    print(request.json)

    if request.json["user_verdict"] == "report":
        event = '$review.escalated'
        return_msg = "report"
    else:
        event = '$challenge.succeeded'
        return_msg = "approve"

    castle = Client.from_request(request)

    payload = {
        'event': event,
        'device_token': request.json["device_token"],
        'context': {}
    }

    payload["context"]["client_id"] = request.json["client_id"]

    result = castle.track(payload)

    print(result)

    r = {
        "api_endpoint": "track",
        "castle_event": event,
        "payload": payload
    }

    return r, 200, {'ContentType':'application/json'}

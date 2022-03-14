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
        "castle_pk": os.getenv('castle_pk'),
        "location": os.getenv('location'),
        "demo_list": demo_list,
        "username": os.getenv("valid_username"),
        "invalid_password": os.getenv("invalid_password"),
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

    if "device_token" in verdict:
        r["device_token"] = verdict["device_token"]

    return r, 200, {'ContentType':'application/json'}

@app.route('/evaluate_new_password', methods=['POST'])
def evaluate_new_password():

    print(request.json)

    password = request.json["password"]
    request_token = request.json["request_token"]

    # check validity of username + password combo
    if password == os.getenv("valid_password"):
        castle_type = "$password"
        castle_status = "$succeeded"
    else:
        castle_type = "$password"
        castle_status = "$failed"

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

    castle = Client.from_request(request)

    r = {
        "api_endpoint": "risk",
        "payload_to_castle": payload_to_castle,
        'type': castle_type,
        'status': castle_status,
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
        castle_type = '$review'
        castle_status = '$escalated'
        return_msg = "report"
    else:
        castle_type = '$challenge'
        castle_status = '$succeeded'

        return_msg = "approve"

    castle = Client.from_request(request)

    payload = {
        'type': castle_type,
        'status': castle_status,
        'device_token': request.json["device_token"],
        'context': {}
    }

    result = castle.risk(payload)

    print(result)

    r = {
        "api_endpoint": "risk",
        "payload": payload
    }

    return r, 200, {'ContentType':'application/json'}

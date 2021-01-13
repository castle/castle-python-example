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
        "username": "lois.lane@mailinator.com" 
    }

    return default_params

# another default value
registered_at = '2020-02-23T22:28:55.387Z'

@app.route('/')
def home():

    params = get_default_params()

    params["home"] = True

    return render_template('index.html', **params)

@app.route('/<demo_name>')
def demo(demo_name):

    if demo_name not in valid_urls:

        return render_template('index.html', error=True)

    ##########################################

    params = get_default_params()

    this_demo = demos[demo_name]

    for k, v in this_demo.items():

        params[k] = v

        params["demo_name"] = demo_name

    return render_template('index.html', **params)

@app.route('/evaluate_login', methods=['POST'])
def evaluate_login():

    print(request.json)

    email = request.json["email"]
    demo_name = request.json["demo_name"]

    client_id = request.json["client_id"]

    user_id = email

    if demo_name == "login_failed_username_invalid":
        user_id = None

    payload_to_castle = {
        'event': demos[demo_name]["castle_name"],
        'user_id': user_id,
        'user_traits': {
            'email': email,
            'registered_at': registered_at
        },
        'context': {
            'client_id': client_id
        }
    }

    castle = Client.from_request(request)

    if demos[demo_name]["api_endpoint"] == "authenticate":
        verdict = castle.authenticate(payload_to_castle)

    elif demos[demo_name]["api_endpoint"] == "track":

        verdict = castle.track(payload_to_castle)

    print("verdict:")
    print(verdict)

    r = {
        "api_endpoint": demos[demo_name]["api_endpoint"],
        "payload_to_castle": payload_to_castle,
        "result": verdict
    }

    if "device_token" in verdict:
        r["device_token"] = verdict["device_token"]

    if "action" in verdict:
        r["action"] = verdict["action"]

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

    result = castle.track(
        {
            'event': event,
            'device_token': request.json["device_token"]
        }
    )

    print(result)

    r = {
        "message": return_msg
    }

    return r, 200, {'ContentType':'application/json'}

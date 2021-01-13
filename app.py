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
# from castle import events
# from castle.api_request import APIRequest
# from castle.commands.get_device import CommandsGetDevice

#################################

import castle_config

#################################

load_dotenv()

app = Flask(__name__)

#################################

demos = {

    "login_failed_password_invalid": {
        "friendly_name": "login failed (password invalid)",
        "castle_name": "$login.failed",
        "api_endpoint": "track",
        "show_password_field": True,
        "show_login_form": True,
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that this is a bad password, so the password does not matter."
    },
    "login_failed_username_invalid": {
        "friendly_name": "login failed (username invalid)",
        "castle_name": "$login.failed",
        "api_endpoint": "track",
        "username": "invalid.username@mailinator.com",
        "show_password_field": True,
        "show_login_form": True,
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that this is an invalid username. You'll see that we send a user_id=null kvp to Castle, to indicate that this request/device included an invalid username."
   },   
    "login_succeeded": {
        "friendly_name": "login succeeded",
        "castle_name": "$login.succeeded",
        "api_endpoint": "authenticate",
        "show_password_field": True,
        "show_login_form": True,
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that the username + password combo is valid. Castle will respond with a recommendation as to whether to allow, deny, or challenge the authentication."
    },
    "password_reset_succeeded": {
        "friendly_name": "password reset succeeded",
        "castle_name": "$password_reset.succeeded",
        "api_endpoint": "track",
        "new_password": True,
        "show_login_form": True,
        "first_step_action": "reset password",
        "first_step_desc": "We're going to assume that the user has arrived on this screen by satisfying whatever challenges you have in place to reset their password. On the back end, Castle will track the successful password reset event."
    },
    "review_suspicious_activity": {
        "api_endpoint": "devices",
        "friendly_name": "review suspicious activity",
        "show_login_form": False,
        "show_password_field": False,
        "first_step_action": "get a device token",
        "first_step_desc": "First, let's get a device token:"
    }
}

#################################

demo_list_global = []

for k, v in demos.items():

    e = {}

    e["url"] = k

    for key, value in v.items():
        e[key] = value

    demo_list_global.append(e)

#################################

valid_urls = []

for k, v in demos.items():
    valid_urls.append(k)

#################################

@app.route('/')
def home():
    castle_app_id = os.getenv('castle_app_id')
    location = os.getenv('location')

    demo_list = demo_list_global

    home = True
    show_header = False

    return render_template('index.html', **locals())

@app.route('/<demo_name>')
def demo(demo_name):

    if demo_name not in valid_urls:
        error = True
        show_form = False
        show_header = False

        return render_template('index.html', **locals())

    ##########################################

    if "username" in demos[demo_name]:
        username = demos[demo_name]["username"]
    else:
        username = "lois.lane@mailinator.com"

    castle_app_id = os.getenv('castle_app_id')
    location = os.getenv('location')

    show_header = True
    show_login_form = demos[demo_name]["show_login_form"]

    if "new_password" in demos[demo_name]:
        new_password = True
    # _password_field = demos[demo_name]["show_password_field"]

    demo_list = demo_list_global

    first_step_action = demos[demo_name]["first_step_action"]
    first_step_desc = demos[demo_name]["first_step_desc"]
    friendly_name = demos[demo_name]["friendly_name"]

    # if demo_name == "forgot_password":
    #     password_field = False
    # else:
    #     password_field = True

    return render_template('index.html', **locals())

@app.route('/evaluate_form_vals', methods=['POST'])
def evaluate_form_vals():

    print(request.json)

    email = request.json["email"]
    demo_name = request.json["demo_name"]

    client_id = request.json["client_id"]

    user_id = email

    if demo_name == "login_failed_username_invalid":
        user_id = None

    registered_at = '2020-02-23T22:28:55.387Z'

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
      'Authorization': 'Basic Okdac0N6cjNlWGhwYzRRYnc2eHVXV016ZlNETHJVWkN4'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

    r = {
        "api_endpoint": "devices",
        "device_info": response.json()
    }

    return r, 200, {'ContentType':'application/json'}

@app.route('/get_device_token', methods=['POST'])
def get_device_token():

    print(request.json)

    ui_state = "<p>got a device token</p>"

    next_step = '<p><button onclick="evaluate_device_token()">get device info</button></p>'

    email = "lois.lane@mailinator.com"

    user_id = email

    registered_at = '2020-02-23T22:28:55.387Z'

    client_id = request.json["client_id"]

    payload_to_castle = {
        'event': "$login_succeeded",
        'user_id': email,
        'user_traits': {
            'email': email,
            'registered_at': registered_at
        },
        'context': {
            'client_id': client_id
        }
    }

    castle = Client.from_request(request)

    verdict = castle.authenticate(payload_to_castle)

    print("verdict:")
    print(verdict)

    r = {
        "api_endpoint": "devices",
        "device_token": verdict["device_token"],
        "payload_to_castle": payload_to_castle,
        "verdict": verdict
    }

    return r, 200, {'ContentType':'application/json'}  

@app.route('/update_device', methods=['POST'])
def update_device():

    print(request.json)

    castle = Client.from_request(request)

    event = '$challenge.succeeded'
    return_msg = "approve"

    if request.json["user_verdict"] == "report":
        event = '$review.escalated'
        return_msg = "report"
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

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
from castle import events

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
        "api_endpoint": "track"
    },
    "login_failed_username_invalid": {
        "friendly_name": "login failed (username invalid)",
        "castle_name": "$login.failed",
        "api_endpoint": "track",
        "username": "invalid.username@mailinator.com"
    },   
    "login_succeeded": {
        "friendly_name": "login succeeded",
        "castle_name": "$login.succeeded",
        "api_endpoint": "authenticate"
    },
    "password_reset_succeeded": {
        "friendly_name": "password reset succeeded",
        "castle_name": "$password_reset.succeeded",
        "api_endpoint": "track"
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

    return render_template('index.html', **locals())

@app.route('/<demo_name>')
def demo(demo_name):

    if demo_name not in valid_urls:
        error = True
        show_form = False
        return render_template('index.html', **locals())

    ##########################################

    if "username" in demos[demo_name]:
        username = demos[demo_name]["username"]
    else:
        username = "lois.lane@mailinator.com"

    castle_app_id = os.getenv('castle_app_id')
    location = os.getenv('location')
    show_form = True

    demo_list = demo_list_global

    friendly_name = demos[demo_name]["friendly_name"]

    if demo_name == "forgot_password":
        password_field = False
    else:
        password_field = True

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
        "endpoint": demos[demo_name]["api_endpoint"],
        "payload": payload_to_castle,
        "result": verdict
    }

    return r, 200, {'ContentType':'application/json'}  

# Castle demo application: Python

This project demonstrates key components of several essential Castle workflows, including login and reviewing a suspicious device. The application is built in Python on Flask/gunicorn.

## How to engage with this application

There are three ways to engage with this application:

1. Visit the public-facing web app: https://castle-demo-python.herokuapp.com
> This is the fastest way to get a sense of what the demo is all about. You do not need a Castle app id or api secret to use the public web app.

2. Clone this repo and install & run locally (more details below)

3. Run a Docker container
> A Dockerfile is included in this repo. Brief instructions for installing locally are below. Or, you can run a container locally immediately from the dockerhub image:

`docker run -d -p 4005:80 -e castle_pk={{castle_pk} -e castle_api_secret={{castle_api_secret}} -e valid_password={{valid_password}} tomgsmith99/castle-demo-python`

## Setting up this application locally

### Set up a Castle tenant

You'll need a Castle tenant to run this app against. If you don't already have a Castle tenant, you can get a free trial at:

https://castle.io

Once you have your Castle tenant set up, you'll need your app ID and API secret to run this app.

### Install the app

This is a Python app built with Python 3.9.1. It has not been tested with other versions of Python.

First, clone the git repo:

`git clone https://github.com/castle/tomsmith-demo-python`

Change to the repo's directory:

`cd castle-demo-python`

Create a virtual environment and activate it:

`python -m venv venv`

`. venv/bin/activate`

Install the dependencies:

`pip install -r requirements.txt`

Copy the `.env_example` file to a file called `.env`

`cp .env_example .env`

Update the `.env` file with your Castle app id and api secret.

`npm install`

`cp node_modules/@castleio/castle-js/dist/castle.browser.js ./static/`

Run the app:
`flask run`
 * Running on http://127.0.0.1:5000/

Note - the app also supports gunicorn:

`gunicorn app:app`

## Docker

### Run from dockerhub

`docker run -d -p 4005:80 -e castle_pk={{castle_pk} -e castle_api_secret={{castle_api_secret}} -e valid_password={{valid_password}} tomgsmith99/castle-demo-python`

### Build image locally

A Dockerfile is included in this repo as well.

You can build a Docker image and run a Docker container as follows:

`docker build -t castle-demo-python .`

`docker run -d -p 4005:80 -e castle_pk={{castle_pk}} -e castle_api_secret={{castle_api_secret}} -e valid_password={{valid_password}} castle-demo-python`

## Disclaimer
I’m sharing this sample app with the hope that other developers find it valuable. Although it is not an officially supported sample, we welcome questions and suggestions at `support@castle.io`.

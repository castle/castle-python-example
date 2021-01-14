#Castle demo application: Python#

This project features and end-to-end sequence for many Castle use-cases, including authentication and reviewing a suspicious device. The application is built in Python on Flask/gunicorn.

##How to engage with this application##

There are three ways to engage with this demo application:

1. Visit the public-facing web app: https://castle-demo-python.herokuapp.com
> This is the fastest way to get a sense of what the demo is all about
> Does not require a Castle app id or api secret

2. Clone this repo and install & run locally (more details below)

3. Run a Docker container
> A Dockerfile is included in this repo. Brief instructions for installing locally are below.
> Or, you can run a container locally immediately from the dockerhub image:

`docker run -d -p 4005:80 -e castle_app_id={{castle_app_id} -e castle_api_secret={{castle_api_secret}} tomgsmith99/castle-demo-python`

##Setting up this application locally##

###Set up a Castle tenant###

You'll need a Castle tenant to run this app against. If you don't already have a Castle tenant, you can get a free trial at:

https://castle.io

Once you have your Castle tenant set up, you'll need your app ID and API secret to run this app.

###Install the app###

This is a Python app built with Python 3.9.1. It has not been tested with other versions of Python.

First, clone the git repo:

`git clone https://github.com/castle/castle-demo-python.git`

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

Run the app:
`flask run`
 * Running on http://127.0.0.1:5000/

Note - the app also support gunicorn:

`gunicorn app:app`

*Docker*
A Dockerfile is included in this repo as well.

You can build a Docker image and run a Docker container as follows:

`docker build -t castle-demo-python .`

`docker run -d -p 4005:80 -e castle_app_id={{castle_app_id}} -e castle_api_secret={{castle_api_secret}} castle-demo-python`

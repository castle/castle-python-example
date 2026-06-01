# Castle demo application: Python

This project demonstrates key components of several essential Castle workflows. It is built in Python on Flask/gunicorn and uses the [castle](https://github.com/castle/castle-python) SDK (7.1).

## What's demonstrated

- **login** – `risk` (successful login) and `filter` (failed login) endpoints
- **password reset** – the non-blocking `log` endpoint
- **lists** – the Lists API (`create_list`, `get_all_lists`)
- **privacy** – the Privacy API (`request_user_data`, `delete_user_data`)
- **events** – the Events API (`events_schema`, `query_events`)

## Prerequisites

You'll need a Castle tenant to run this app against. If you don't already have one, you can start a free trial at https://castle.io.

From your Castle dashboard you'll need two values:

- your **publishable key** (`pk`) – used by the browser SDK
- your **API secret** – used by the backend SDK

## Running locally

This is a Python app. The castle 7.1 SDK requires **Python 3.9 or newer**; this demo is tested with Python 3.13.

Clone the repo and change into it:

```bash
git clone https://github.com/castle/castle-python-example.git
cd castle-python-example
```

Create and activate a virtual environment:

```bash
python -m venv venv
. venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Fetch the browser SDK asset (served at `/static/castle.browser.js`):

```bash
npm install
cp node_modules/@castleio/castle-js/dist/castle.browser.js ./static/
```

Create your `.env` from the example and fill in your Castle publishable key (`castle_pk`), API secret (`castle_api_secret`) and a `valid_password`:

```bash
cp .env_example .env
```

Run the app:

```bash
flask run
# Running on http://127.0.0.1:5000/
```

The app also runs under gunicorn:

```bash
gunicorn app:app
```

## Running with Docker

The bundled `Dockerfile` builds from local source and serves the app with gunicorn on port 80. Because the browser SDK asset is fetched via npm (and is not committed), run the `npm install` + copy step above **before** building the image.

Build the image:

```bash
docker build -t castle-demo-python .
```

Run a container. The non-secret demo values (`valid_username`, `valid_user_id`, etc.) are baked into the image, so you only need to pass your secrets:

```bash
docker run -d -p 4005:80 \
  -e castle_pk=YOUR_PUBLISHABLE_KEY \
  -e castle_api_secret=YOUR_API_SECRET \
  -e valid_password=YOUR_VALID_PASSWORD \
  castle-demo-python
```

The app will be available at http://127.0.0.1:4005.

## Disclaimer

I’m sharing this sample app with the hope that other developers find it valuable. Although it is not an officially supported sample, we welcome questions and suggestions at `support@castle.io`.

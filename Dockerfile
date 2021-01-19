FROM tiangolo/meinheld-gunicorn-flask:python3.7

WORKDIR /tmp

RUN git clone git://github.com/castle/castle-demo-python

WORKDIR /tmp/castle-demo-python

RUN mv * /app

WORKDIR /app

RUN mv app.py main.py

##############################################

ENV location=docker
ENV valid_password={{valid_password}}
ENV valid_username=clark.kent@dailyplanet.com
ENV valid_user_id=00000000
ENV webhook_url=https://webhook.site

RUN pip install castle
RUN pip install python-dotenv
RUN pip install requests

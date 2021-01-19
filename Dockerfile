FROM tiangolo/meinheld-gunicorn-flask:python3.7

WORKDIR /tmp

RUN git clone git://github.com/castle/castle-demo-python

WORKDIR /tmp/castle-demo-python

RUN mv * /app

WORKDIR /app

RUN mv app.py main.py

##############################################

ENV location=docker

RUN pip install castle
RUN pip install python-dotenv
RUN pip install requests

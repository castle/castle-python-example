FROM tiangolo/meinheld-gunicorn-flask:python3.7

ENV VERSION=1.0
ENV TARBALL=v${VERSION}.tar.gz
ENV RELEASE=tomsmith-demo-python-${VERSION}

WORKDIR /tmp

ADD https://github.com/castle/tomsmith-demo-python/archive/${TARBALL} ${TARBALL}

RUN tar -xzf ${TARBALL}

RUN rm ${TARBALL}

RUN rm -r /app

RUN mv ${RELEASE} /app

WORKDIR /app

RUN mv app.py main.py

##############################################

ENV location=docker
ENV invalid_password={{invalid_password}}
ENV valid_password={{valid_password}}
ENV valid_username=clark.kent@dailyplanet.com
ENV valid_user_id=00000000
ENV webhook_url=https://webhook.site

RUN pip install castle
RUN pip install python-dotenv
RUN pip install requests

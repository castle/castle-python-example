# Fetch the Castle browser SDK from npm (served at runtime from node_modules).
FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /app/node_modules ./node_modules

ENV location=docker
ENV PORT=80

# Non-secret demo defaults. Supply castle_pk, castle_api_secret and
# valid_password at runtime (e.g. docker run -e ...).
ENV invalid_password=qwerty
ENV valid_username=clark.kent@dailyplanet.com
ENV valid_user_id=00000000
ENV webhook_url=https://webhook.site

EXPOSE 80

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT}"]

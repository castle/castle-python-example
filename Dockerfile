FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

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

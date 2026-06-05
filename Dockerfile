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

# Only the Castle credentials are needed at runtime (e.g. docker run -e ...);
# the simulated demo user values are baked in as code defaults.

EXPOSE 80

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT}"]

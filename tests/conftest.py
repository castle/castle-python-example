"""Shared pytest fixtures for the Castle demo app.

The Castle SDK is always mocked in these tests so the suite never makes a real
network call. We set deterministic env defaults *before* importing ``app`` so
that ``castle_config`` and the route handlers see stable values regardless of
the developer's local ``.env``.
"""
import os

import pytest

# Deterministic env, applied before `app` is imported below.
TEST_ENV = {
    "castle_api_secret": "test_secret",
    "castle_pk": "pk_test",
    "location": "test",
    "valid_username": "clark.kent@dailyplanet.com",
    "valid_password": "supersecret",
    "valid_user_id": "00000000",
    "invalid_password": "qwerty",
    "webhook_url": "https://webhook.site",
}
for key, value in TEST_ENV.items():
    os.environ[key] = value

import app as app_module  # noqa: E402  (must follow the env setup above)

# The known-good registration date the app uses as a module-level default. The
# `evaluate_login` handler mutates this global, so we restore it before each test.
DEFAULT_REGISTERED_AT = "2020-02-23T22:28:55.387Z"


@pytest.fixture
def app():
    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset the mutable module-level state the handlers touch."""
    app_module.registered_at = DEFAULT_REGISTERED_AT
    app_module.received_webhooks.clear()
    yield
    app_module.registered_at = DEFAULT_REGISTERED_AT
    app_module.received_webhooks.clear()

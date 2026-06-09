"""Tests for how the app integrates with the Castle SDK.

The SDK ``Client`` is mocked everywhere, so these assert *how* the app calls the
SDK (which endpoint, with what payload) and how it handles ``CastleError`` —
not the SDK's own behavior or any live API.

Two seams are patched:
- ``app.Client`` for the request-scoped flows (login / password reset), which
  build the client via ``Client.from_request(request)``.
- ``app.castle_client`` for the account-level flows (lists / privacy / events).
"""
from unittest.mock import MagicMock, patch

import pytest

from castle.errors import CastleError, WebhookVerificationError

import app as app_module


def _post(client, path, payload):
    return client.post(path, json=payload)


@pytest.fixture
def fake_sdk():
    """A mock Castle client wired into both client-creation seams."""
    fake = MagicMock(name="castle_client")
    with patch.object(app_module, "Client") as mock_client_cls, \
            patch.object(app_module, "castle_client", return_value=fake):
        mock_client_cls.from_request.return_value = fake
        yield fake


# ---------------------------------------------------------------------------
# Risk / filter (login)
# ---------------------------------------------------------------------------
class TestEvaluateLogin:
    def test_valid_credentials_filter_attempt_then_risk(self, client, fake_sdk):
        fake_sdk.filter.return_value = {"policy": {"action": "allow"}}
        fake_sdk.risk.return_value = {"policy": {"action": "allow"}}

        resp = _post(client, "/evaluate_login", {
            "email": "clark.kent@dailyplanet.com",
            "password": "supersecret",
            "request_token": "tok-123",
        })

        assert resp.status_code == 200
        steps = resp.get_json()["steps"]
        assert len(steps) == 2

        attempt, outcome = steps
        assert attempt["api_endpoint"] == "filter"
        assert attempt["castle_status"] == "$attempted"
        assert attempt["payload_to_castle"]["params"]["email"] == "clark.kent@dailyplanet.com"

        assert outcome["api_endpoint"] == "risk"
        assert outcome["castle_status"] == "$succeeded"

        fake_sdk.filter.assert_called_once()
        fake_sdk.risk.assert_called_once()
        sent = fake_sdk.risk.call_args.args[0]
        assert sent["type"] == "$login"
        assert sent["status"] == "$succeeded"
        assert sent["user"]["id"] == "00000000"
        assert sent["user"]["email"] == "clark.kent@dailyplanet.com"
        assert sent["user"]["registered_at"]
        assert sent["request_token"] == "tok-123"

    def test_wrong_password_filters_failure_with_matching_user(self, client, fake_sdk):
        fake_sdk.filter.return_value = {"policy": {"action": "deny"}}

        resp = _post(client, "/evaluate_login", {
            "email": "clark.kent@dailyplanet.com",
            "password": "wrong-password",
            "request_token": "tok-456",
        })

        outcome = resp.get_json()["steps"][1]
        assert outcome["api_endpoint"] == "filter"
        assert outcome["castle_status"] == "$failed"

        assert fake_sdk.filter.call_count == 2
        fake_sdk.risk.assert_not_called()
        sent = outcome["payload_to_castle"]
        assert sent["params"]["email"] == "clark.kent@dailyplanet.com"
        assert sent["matching_user_id"] == "00000000"

    def test_unknown_user_filters_failure_without_matching_user(self, client, fake_sdk):
        fake_sdk.filter.return_value = {"policy": {"action": "deny"}}

        resp = _post(client, "/evaluate_login", {
            "email": "stranger@example.com",
            "password": "whatever",
            "request_token": "tok-789",
        })

        outcome = resp.get_json()["steps"][1]
        assert outcome["api_endpoint"] == "filter"
        assert outcome["castle_status"] == "$failed"
        sent = outcome["payload_to_castle"]
        assert sent["params"]["email"] == "stranger@example.com"
        assert "matching_user_id" not in sent


# ---------------------------------------------------------------------------
# Filter (registration)
# ---------------------------------------------------------------------------
class TestEvaluateSignup:
    def test_new_email_filtered_as_attempted(self, client, fake_sdk):
        fake_sdk.filter.return_value = {"policy": {"action": "allow"}}

        resp = _post(client, "/evaluate_signup", {
            "name": "Lois Lane",
            "email": "lois.lane@dailyplanet.com",
            "request_token": "tok-1",
        })

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["api_endpoint"] == "filter"
        assert body["castle_type"] == "$registration"
        assert body["castle_status"] == "$attempted"
        fake_sdk.filter.assert_called_once()
        fake_sdk.risk.assert_not_called()
        sent = fake_sdk.filter.call_args.args[0]
        assert sent["params"]["email"] == "lois.lane@dailyplanet.com"
        assert "user" not in sent
        assert "matching_user_id" not in sent

    def test_existing_email_filtered_as_failed(self, client, fake_sdk):
        fake_sdk.filter.return_value = {"policy": {"action": "deny"}}

        resp = _post(client, "/evaluate_signup", {
            "name": "Clark Kent",
            "email": "clark.kent@dailyplanet.com",
            "request_token": "tok-2",
        })

        body = resp.get_json()
        assert body["api_endpoint"] == "filter"
        assert body["castle_status"] == "$failed"
        fake_sdk.filter.assert_called_once()
        fake_sdk.risk.assert_not_called()
        sent = fake_sdk.filter.call_args.args[0]
        assert sent["params"]["email"] == "clark.kent@dailyplanet.com"
        assert sent["matching_user_id"] == "00000000"


# ---------------------------------------------------------------------------
# Risk (profile update)
# ---------------------------------------------------------------------------
class TestEvaluateProfileUpdate:
    def test_profile_update_calls_risk(self, client, fake_sdk):
        fake_sdk.risk.return_value = {"policy": {"action": "allow"}}

        resp = _post(client, "/evaluate_profile_update", {
            "name": "Kal-El",
            "email": "kal.el@dailyplanet.com",
            "request_token": "tok-3",
        })

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["api_endpoint"] == "risk"
        assert body["castle_type"] == "$profile_update"
        fake_sdk.risk.assert_called_once()
        sent = fake_sdk.risk.call_args.args[0]
        assert sent["user"]["name"] == "Kal-El"
        assert sent["user"]["email"] == "kal.el@dailyplanet.com"


# ---------------------------------------------------------------------------
# Log (logout)
# ---------------------------------------------------------------------------
class TestEvaluateLogout:
    def test_logout_logs_event(self, client, fake_sdk):
        resp = _post(client, "/evaluate_logout", {"request_token": "tok-4"})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["api_endpoint"] == "log"
        assert body["castle_type"] == "$logout"
        fake_sdk.log.assert_called_once()
        assert fake_sdk.log.call_args.args[0]["type"] == "$logout"


# ---------------------------------------------------------------------------
# Log (password reset)
# ---------------------------------------------------------------------------
class TestEvaluateNewPassword:
    def test_new_password_logs_succeeded(self, client, fake_sdk):
        resp = _post(client, "/evaluate_new_password", {
            "password": "a-brand-new-password",
            "request_token": "tok-1",
        })

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["api_endpoint"] == "log"
        assert body["status"] == "$succeeded"

        fake_sdk.log.assert_called_once()
        sent = fake_sdk.log.call_args.args[0]
        assert sent["type"] == "$password_reset"
        assert sent["status"] == "$succeeded"
        assert sent["user"]["email"] == "clark.kent@dailyplanet.com"

    def test_reusing_current_password_logs_failed(self, client, fake_sdk):
        resp = _post(client, "/evaluate_new_password", {
            "password": "supersecret",
            "request_token": "tok-2",
        })

        body = resp.get_json()
        assert body["status"] == "$failed"
        fake_sdk.log.assert_called_once()
        assert fake_sdk.log.call_args.args[0]["status"] == "$failed"


# ---------------------------------------------------------------------------
# Lists API
# ---------------------------------------------------------------------------
class TestCreateList:
    def test_defaults_create_then_fetch(self, client, fake_sdk):
        fake_sdk.create_list.return_value = {"id": "list-1"}
        fake_sdk.get_all_lists.return_value = [{"id": "list-1"}]

        resp = _post(client, "/create_list", {})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["api_endpoint"] == "lists"
        assert body["payload_to_castle"] == {
            "name": "demo-blocklist",
            "color": "$red",
            "primary_field": "user.email",
        }
        assert body["result"]["created"] == {"id": "list-1"}
        assert body["result"]["all_lists"] == [{"id": "list-1"}]
        fake_sdk.create_list.assert_called_once()
        fake_sdk.get_all_lists.assert_called_once()

    def test_custom_payload_is_forwarded(self, client, fake_sdk):
        fake_sdk.create_list.return_value = {"id": "list-2"}
        fake_sdk.get_all_lists.return_value = []

        resp = _post(client, "/create_list", {
            "name": "vip",
            "color": "$green",
            "primary_field": "user.id",
        })

        sent = fake_sdk.create_list.call_args.args[0]
        assert sent == {"name": "vip", "color": "$green", "primary_field": "user.id"}
        assert resp.get_json()["payload_to_castle"] == sent

    def test_castle_error_is_handled(self, client, fake_sdk):
        fake_sdk.create_list.side_effect = CastleError("list blew up")

        resp = _post(client, "/create_list", {})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["result"] == {"error": "list blew up"}
        fake_sdk.get_all_lists.assert_not_called()


# ---------------------------------------------------------------------------
# Privacy API
# ---------------------------------------------------------------------------
class TestPrivacyUserData:
    def test_default_action_requests_data(self, client, fake_sdk):
        fake_sdk.request_user_data.return_value = {"status": "ok"}

        resp = _post(client, "/privacy_user_data", {})

        body = resp.get_json()
        assert body["api_endpoint"] == "privacy (request)"
        assert body["payload_to_castle"] == {
            "identifier": "clark.kent@dailyplanet.com",
            "identifier_type": "$email",
        }
        fake_sdk.request_user_data.assert_called_once()
        fake_sdk.delete_user_data.assert_not_called()

    def test_delete_action_deletes_data(self, client, fake_sdk):
        fake_sdk.delete_user_data.return_value = {"status": "deleted"}

        resp = _post(client, "/privacy_user_data", {
            "action": "delete",
            "identifier": "someone@else.com",
            "identifier_type": "$user_id",
        })

        body = resp.get_json()
        assert body["api_endpoint"] == "privacy (delete)"
        assert body["payload_to_castle"] == {
            "identifier": "someone@else.com",
            "identifier_type": "$user_id",
        }
        fake_sdk.delete_user_data.assert_called_once()
        fake_sdk.request_user_data.assert_not_called()

    def test_castle_error_is_handled(self, client, fake_sdk):
        fake_sdk.request_user_data.side_effect = CastleError("privacy failure")

        resp = _post(client, "/privacy_user_data", {})

        body = resp.get_json()
        assert body["api_endpoint"] == "privacy"
        assert body["result"] == {"error": "privacy failure"}


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------
class TestWebhooks:
    def test_verified_webhook_is_stored_and_listed(self, client):
        with patch.object(app_module, "WebhooksVerify") as mock_verify:
            mock_verify.call.return_value = None

            resp = client.post(
                "/webhooks/castle",
                json={"type": "review.opened", "data": {"id": "rev_1"}},
                headers={"X-Castle-Signature": "valid"},
            )

            assert resp.status_code == 204
            mock_verify.call.assert_called_once()

        listing = client.get("/webhooks")
        assert listing.status_code == 200
        assert b"review.opened" in listing.data

    def test_unverified_webhook_is_rejected(self, client):
        with patch.object(app_module, "WebhooksVerify") as mock_verify:
            mock_verify.call.side_effect = WebhookVerificationError("bad signature")

            resp = client.post(
                "/webhooks/castle",
                json={"type": "review.opened"},
                headers={"X-Castle-Signature": "bad"},
            )

            assert resp.status_code == 404

        listing = client.get("/webhooks")
        assert b"No webhooks received yet." in listing.data

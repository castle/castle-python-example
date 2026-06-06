"""Smoke tests for the rendered demo pages."""
import pytest

from demo_config import valid_urls


def test_home_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<html" in resp.data.lower()


@pytest.mark.parametrize("demo_name", valid_urls)
def test_every_demo_page_renders(client, demo_name):
    resp = client.get(f"/{demo_name}")
    assert resp.status_code == 200
    assert b"<html" in resp.data.lower()


def test_demo_list_matches_config():
    # Guards against the demo list and the URL allowlist drifting apart.
    assert set(valid_urls) == {
        "signup", "login", "account", "password_reset", "lists", "privacy",
        "webhooks"
    }


def test_unknown_demo_renders_error_page(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 200
    # error.html is served instead of a demo template.
    assert b"<html" in resp.data.lower()


def test_unknown_vendor_asset_returns_404(client):
    resp = client.get("/vendor/castle-js/nope.js")
    assert resp.status_code == 404

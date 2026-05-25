import pytest
import json
from unittest.mock import patch, MagicMock
from tests.conftest import *  # noqa

def auth_header(client, email="a@b.com"):
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_billing_status_free(client):
    h = auth_header(client)
    r = client.get("/billing/status", headers=h)
    assert r.status_code == 200
    assert r.json()["plan"] == "free"

def test_checkout_requires_auth(client):
    r = client.post("/billing/checkout", json={"plan": "pro"})
    assert r.status_code == 401

def test_checkout_creates_session(client):
    h = auth_header(client)
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/fake"
    mock_customer = MagicMock()
    mock_customer.id = "cus_fake123"

    with patch("backend.api.billing.stripe") as mock_stripe, \
         patch("backend.api.billing.settings") as mock_settings:
        mock_settings.stripe_pro_price_id = "price_pro_test"
        mock_settings.stripe_agency_price_id = "price_agency_test"
        mock_settings.frontend_url = "http://localhost:3000"
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.checkout.Session.create.return_value = mock_session
        r = client.post("/billing/checkout", json={"plan": "pro"}, headers=h)

    assert r.status_code == 200
    assert r.json()["checkout_url"] == "https://checkout.stripe.com/fake"

def test_webhook_subscription_created(client):
    h = auth_header(client)
    r = client.get("/workspaces/me", headers=h)
    workspace_id = r.json()["id"]

    payload = json.dumps({
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_fake123",
                "status": "active",
                "metadata": {"workspace_id": str(workspace_id)},
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        }
    }).encode()

    with patch("backend.api.billing.stripe.Webhook.construct_event") as mock_verify:
        mock_verify.return_value = json.loads(payload)
        r = client.post(
            "/billing/webhook",
            content=payload,
            headers={"stripe-signature": "fake_sig", "content-type": "application/json"},
        )
    assert r.status_code == 200

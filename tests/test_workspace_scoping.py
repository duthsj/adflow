import pytest
from tests.conftest import *  # noqa


def register_and_login(client, email, name="Test"):
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": name})
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def create_client_api(client, headers, name="TestCo"):
    return client.post("/clients", json={
        "name": name,
        "industry": "Tech",
        "brand_guidelines": {"tone": "professional", "colors": [], "fonts": [], "keywords": []},
        "social_accounts": {"instagram": None, "facebook": None, "tiktok": None, "linkedin": None, "twitter": None},
    }, headers=headers)


def test_client_list_isolated_by_workspace(client):
    h_a = register_and_login(client, "a@scope.com", "UserA")
    h_b = register_and_login(client, "b@scope.com", "UserB")

    create_client_api(client, h_a, "Client of A")

    r_a = client.get("/clients", headers=h_a)
    r_b = client.get("/clients", headers=h_b)

    assert len(r_a.json()) == 1
    assert len(r_b.json()) == 0


def test_client_get_isolated_by_workspace(client):
    h_a = register_and_login(client, "c@scope.com", "UserC")
    h_b = register_and_login(client, "d@scope.com", "UserD")

    r = create_client_api(client, h_a, "Private Client")
    client_id = r.json()["id"]

    r_b = client.get(f"/clients/{client_id}", headers=h_b)
    assert r_b.status_code == 404


def test_client_create_sets_workspace(client):
    h = register_and_login(client, "e@scope.com", "UserE")
    r = create_client_api(client, h, "MyClient")
    assert r.status_code == 200
    client_id = r.json()["id"]

    r_list = client.get("/clients", headers=h)
    ids = [c["id"] for c in r_list.json()]
    assert client_id in ids


def test_workspace_isolation_update(client):
    h_a = register_and_login(client, "f@scope.com", "UserF")
    h_b = register_and_login(client, "g@scope.com", "UserG")

    r = create_client_api(client, h_a, "UpdateTarget")
    client_id = r.json()["id"]

    r_update = client.put(f"/clients/{client_id}", json={"name": "Hacked"}, headers=h_b)
    assert r_update.status_code == 404


def test_billing_status_requires_workspace(client):
    # No auth: verify 401 is returned
    r = client.get("/billing/status")
    assert r.status_code == 401


def test_workspace_name_persists(client):
    h = register_and_login(client, "h@scope.com", "UserH")
    client.put("/workspaces/me", json={"name": "Renamed Agency"}, headers=h)
    r = client.get("/workspaces/me", headers=h)
    assert r.json()["name"] == "Renamed Agency"

import pytest
from tests.conftest import *  # noqa

def register_and_login(client, email="a@b.com"):
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_register_creates_workspace(client):
    h = register_and_login(client)
    r = client.get("/workspaces/me", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] is not None
    assert data["plan"] == "free"

def test_update_workspace_name(client):
    h = register_and_login(client)
    r = client.put("/workspaces/me", json={"name": "My Agency"}, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "My Agency"

def test_workspace_members_includes_owner(client):
    h = register_and_login(client)
    r = client.get("/workspaces/me/members", headers=h)
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"

def test_invite_and_accept(client):
    h_owner = register_and_login(client, "owner@b.com")
    r = client.post("/workspaces/me/invite", headers=h_owner)
    assert r.status_code == 200
    token = r.json()["invite_token"]

    client.post("/auth/register", json={"email": "guest@b.com", "password": "pass1234", "name": "Guest"})
    h_guest = register_and_login(client, "guest@b.com")
    r = client.post(f"/workspaces/accept-invite/{token}", headers=h_guest)
    assert r.status_code == 200

    r = client.get("/workspaces/me/members", headers=h_owner)
    assert len(r.json()) == 2

def test_workspace_requires_auth(client):
    r = client.get("/workspaces/me")
    assert r.status_code == 401

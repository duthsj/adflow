import pytest
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_analytics_summary_empty(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.get(f"/analytics/summary?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total_posts"] == 0
    assert data["pending_approvals"] == 0

def test_analytics_by_platform_empty(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.get(f"/analytics/by-platform?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    assert r.json() == []

def test_analytics_requires_auth(client):
    r = client.get("/analytics/summary?client_id=1&period=week")
    assert r.status_code == 401

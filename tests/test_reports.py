import pytest
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_generate_report_returns_pdf(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.post(
        "/reports/generate",
        json={"client_id": client_id, "period": "week", "include_insights": False},
        headers=h,
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

def test_generate_report_unknown_client(client):
    h = auth_header(client)
    r = client.post(
        "/reports/generate",
        json={"client_id": 999, "period": "week", "include_insights": False},
        headers=h,
    )
    assert r.status_code == 404

def test_report_requires_auth(client):
    r = client.post("/reports/generate", json={"client_id": 1, "period": "week", "include_insights": False})
    assert r.status_code == 401

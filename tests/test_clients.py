import pytest

def get_token(client):
    client.post("/auth/register", json={
        "email": "admin@muelaads.com", "password": "password123",
        "name": "Admin", "role": "admin"
    })
    r = client.post("/auth/login", json={"email": "admin@muelaads.com", "password": "password123"})
    return r.json()["access_token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def test_create_client(client):
    token = get_token(client)
    response = client.post("/clients", json={
        "name": "Acme Corp",
        "industry": "Technology",
        "brand_guidelines": {"tone": "professional", "colors": ["#000", "#fff"], "fonts": [], "keywords": [], "avoid": []},
        "social_accounts": {"instagram": "@acme"}
    }, headers=auth(token))
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corp"

def test_list_clients(client):
    token = get_token(client)
    client.post("/clients", json={"name": "Test Co", "industry": "Retail"}, headers=auth(token))
    r = client.get("/clients", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_get_client(client):
    token = get_token(client)
    created = client.post("/clients", json={"name": "Get Co", "industry": "Food"}, headers=auth(token)).json()
    r = client.get(f"/clients/{created['id']}", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["name"] == "Get Co"

def test_update_client(client):
    token = get_token(client)
    created = client.post("/clients", json={"name": "Old Name", "industry": "Tech"}, headers=auth(token)).json()
    r = client.put(f"/clients/{created['id']}", json={"name": "New Name"}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"

def test_get_client_not_found(client):
    token = get_token(client)
    r = client.get("/clients/99999", headers=auth(token))
    assert r.status_code == 404

def test_list_requires_auth(client):
    r = client.get("/clients")
    assert r.status_code in (401, 403)

import pytest
import io
from unittest.mock import patch
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def make_client(client, h):
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    return r.json()["id"]

def test_asset_list_empty(client):
    h = auth_header(client)
    client_id = make_client(client, h)
    r = client.get(f"/assets?client_id={client_id}", headers=h)
    assert r.status_code == 200
    assert r.json() == []

def test_asset_upload(client):
    h = auth_header(client)
    client_id = make_client(client, h)

    with patch("backend.api.assets.r2_upload") as mock_upload:
        mock_upload.return_value = "assets/test-key.png"
        file_data = io.BytesIO(b"fake image data")
        r = client.post(
            "/assets/upload",
            data={"client_id": str(client_id), "asset_type": "image"},
            files={"file": ("test.png", file_data, "image/png")},
            headers=h,
        )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.png"
    assert data["type"] == "image"
    assert data["client_id"] == client_id

def test_asset_delete(client):
    h = auth_header(client)
    client_id = make_client(client, h)

    with patch("backend.api.assets.r2_upload") as mock_upload, \
         patch("backend.api.assets.r2_delete") as mock_delete:
        mock_upload.return_value = "assets/key.png"
        mock_delete.return_value = None
        file_data = io.BytesIO(b"data")
        r = client.post(
            "/assets/upload",
            data={"client_id": str(client_id), "asset_type": "image"},
            files={"file": ("img.png", file_data, "image/png")},
            headers=h,
        )
        asset_id = r.json()["id"]
        r = client.delete(f"/assets/{asset_id}", headers=h)
    assert r.status_code == 204

def test_asset_requires_auth(client):
    r = client.get("/assets?client_id=1")
    assert r.status_code == 401

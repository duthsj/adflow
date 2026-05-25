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

def test_analytics_summary_counts_content(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.post("/projects", json={
        "client_id": client_id, "title": "P1", "service_type": "social_media"
    }, headers=h)
    project_id = r.json()["id"]

    from unittest.mock import patch
    with patch("backend.api.content.generate_content", return_value="Test content"):
        client.post("/content/generate", json={
            "project_id": project_id, "content_type": "instagram_post", "instructions": "test"
        }, headers=h)

    r = client.get(f"/analytics/summary?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    assert r.json()["total_posts"] == 1
    assert r.json()["pending_approvals"] == 1

def test_analytics_by_platform_aggregates(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]

    from backend.models.analytics import Analytics
    from tests.conftest import TestingSession
    db = TestingSession()
    db.add(Analytics(client_id=client_id, platform="instagram", metric_type="posts", value=5.0))
    db.add(Analytics(client_id=client_id, platform="instagram", metric_type="reach", value=1000.0))
    db.commit()
    db.close()

    r = client.get(f"/analytics/by-platform?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["platform"] == "instagram"
    assert data[0]["posts"] == 5
    assert data[0]["reach"] == 1000.0

from unittest.mock import patch

def test_analytics_insights(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]

    mock_response = type("R", (), {
        "content": [type("C", (), {"text": "Tip 1. Tip 2. Tip 3."})()]
    })()

    with patch("backend.api.analytics._get_client") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_response
        r = client.post("/analytics/insights", json={"client_id": client_id, "period": "week"}, headers=h)
    assert r.status_code == 200
    assert "insights" in r.json()
    assert len(r.json()["insights"]) > 0

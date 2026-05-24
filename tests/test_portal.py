import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.models.approval_token import ApprovalToken

def test_approval_token_model_exists():
    assert hasattr(ApprovalToken, "__tablename__")
    assert ApprovalToken.__tablename__ == "approval_tokens"

def test_approval_token_has_required_fields():
    cols = {c.name for c in ApprovalToken.__table__.columns}
    assert "id" in cols
    assert "token" in cols
    assert "client_id" in cols
    assert "project_id" in cols
    assert "expires_at" in cols
    assert "created_by" in cols
    assert "active" in cols


def get_auth_and_client(http_client):
    http_client.post("/auth/register", json={
        "email": "portal_admin@m.com", "password": "password123", "name": "Admin", "role": "admin"
    })
    token = http_client.post("/auth/login", json={
        "email": "portal_admin@m.com", "password": "password123"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    c = http_client.post("/clients", json={"name": "Portal Client", "industry": "Tech"}, headers=headers).json()
    return headers, c, token

def test_create_portal_token(client):
    headers, c, _ = get_auth_and_client(client)
    r = client.post(f"/clients/{c['id']}/portal-token", json={"expires_hours": 48}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["client_id"] == c["id"]
    assert "/portal/" in data["portal_url"]

def test_portal_view_empty(client):
    headers, c, _ = get_auth_and_client(client)
    r_token = client.post(f"/clients/{c['id']}/portal-token", json={}, headers=headers).json()
    r = client.get(f"/portal/{r_token['token']}")
    assert r.status_code == 200
    assert r.json()["content_items"] == []

def test_portal_invalid_token(client):
    r = client.get("/portal/nonexistent-token-12345")
    assert r.status_code == 404

def test_portal_approve_content(client):
    headers, c, _ = get_auth_and_client(client)
    proj = client.post("/projects", json={
        "client_id": c["id"], "title": "P", "service_type": "social_media"
    }, headers=headers).json()

    from unittest.mock import patch, MagicMock
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Test content for portal")]
    with patch("backend.agents.social_agent._get_client") as mock_get:
        mock_get.return_value = MagicMock(**{"messages.create.return_value": mock_msg})
        content_item = client.post("/content/generate", json={
            "project_id": proj["id"], "content_type": "post"
        }, headers=headers).json()

    # Admin approves content first (draft → approved)
    client.post("/content/approve", json={"content_id": content_item["id"]}, headers=headers)

    portal_token = client.post(f"/clients/{c['id']}/portal-token", json={}, headers=headers).json()
    r = client.get(f"/portal/{portal_token['token']}")
    assert r.status_code == 200
    items = r.json()["content_items"]
    assert len(items) == 1
    r_approve = client.post(f"/portal/{portal_token['token']}/approve", json={"content_id": items[0]["id"]})
    assert r_approve.status_code == 200

from unittest.mock import patch, MagicMock
from backend.agents.social_agent import generate_social_post

def test_generate_social_post_calls_claude():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Exciting new product! #innovation #tech")]

    with patch("backend.agents.social_agent._client.messages.create", return_value=mock_message):
        result = generate_social_post(
            brand_guidelines={"tone": "energetic", "keywords": ["innovation"], "avoid": [], "colors": []},
            content_type="post",
            client_name="Acme Corp",
            instructions="Focus on our new product launch"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_social_post_returns_string():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Test post content #hashtag")]

    with patch("backend.agents.social_agent._client.messages.create", return_value=mock_message):
        result = generate_social_post(
            brand_guidelines={},
            content_type="story",
            client_name="Test Client"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_content_generate_endpoint(client):
    """Test the /content/generate endpoint with mocked Claude API."""
    # Setup: register, create client + social_media project
    client.post("/auth/register", json={"email": "c@m.com", "password": "password123", "name": "C", "role": "admin"})
    token = client.post("/auth/login", json={"email": "c@m.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cli = client.post("/clients", json={"name": "Brand Co", "industry": "Tech"}, headers=headers).json()
    proj = client.post("/projects", json={"client_id": cli["id"], "title": "SM Campaign", "service_type": "social_media"}, headers=headers).json()

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Amazing content! #brand #tech")]

    with patch("backend.agents.social_agent._client.messages.create", return_value=mock_message):
        r = client.post("/content/generate", json={
            "project_id": proj["id"],
            "content_type": "post",
            "instructions": "make it exciting"
        }, headers=headers)

    assert r.status_code == 200
    assert r.json()["body"] == "Amazing content! #brand #tech"
    assert r.json()["ai_generated"] is True
    assert r.json()["status"] == "draft"

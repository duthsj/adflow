from unittest.mock import patch, MagicMock
from backend.agents.social_agent import generate_social_post
from backend.agents.ads_agent import generate_ads_copy

def test_generate_social_post_calls_claude():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Exciting new product! #innovation #tech")]

    with patch("backend.agents.social_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
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

    with patch("backend.agents.social_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
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

    with patch("backend.agents.social_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        r = client.post("/content/generate", json={
            "project_id": proj["id"],
            "content_type": "post",
            "instructions": "make it exciting"
        }, headers=headers)

    assert r.status_code == 200
    assert r.json()["body"] == "Amazing content! #brand #tech"
    assert r.json()["ai_generated"] is True
    assert r.json()["status"] == "draft"

def test_ads_agent_returns_string():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="50% off this weekend only. Shop now. #sale")]

    with patch("backend.agents.ads_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_ads_copy(
            brand_guidelines={"tone": "urgent", "keywords": ["sale", "offer"], "avoid": []},
            content_type="facebook_ad",
            client_name="Test Brand",
            instructions="Weekend flash sale 50% off"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_ads_agent_generates_ab_variants():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="VERSION A:\nBuy now!\n\nVERSION B:\nShop today!")]

    with patch("backend.agents.ads_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_ads_copy(
            brand_guidelines={},
            content_type="ab_test",
            client_name="Brand X"
        )

    assert isinstance(result, str)
    assert "VERSION A:" in result
    assert "VERSION B:" in result

def test_seo_agent_returns_string():
    from backend.agents.seo_agent import generate_seo_content

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="# 10 Best Tips for...\n\nIntroduction...")]

    with patch("backend.agents.seo_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_seo_content(
            brand_guidelines={"tone": "informative", "keywords": ["tips", "guide"], "avoid": []},
            content_type="blog_post",
            client_name="Tech Blog",
            instructions="Write about productivity tips"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_seo_agent_meta_tags():
    from backend.agents.seo_agent import generate_seo_content

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Title: Best Tips | Description: Learn the best tips...")]

    with patch("backend.agents.seo_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_seo_content(
            brand_guidelines={},
            content_type="meta_tags",
            client_name="Brand",
            instructions="Product page for running shoes"
        )

    assert isinstance(result, str)

from unittest.mock import patch, MagicMock
from backend.agents.social_agent import generate_social_post
from backend.agents.ads_agent import generate_ads_copy
from backend.agents.seo_agent import generate_seo_content
from backend.agents.design_agent import generate_design_brief
from backend.agents.video_agent import generate_video_content
from backend.agents.orchestrator import generate_content as orch_generate

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

def test_design_agent_returns_string():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="PROMPT: A minimalist product photo with warm tones...\nSTYLE: Clean, modern\nCOLORS: #FF5733, #FFFFFF")]

    with patch("backend.agents.design_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_design_brief(
            brand_guidelines={"tone": "minimalist", "colors": ["#FF5733"], "keywords": [], "avoid": []},
            content_type="image_prompt",
            client_name="Modern Brand",
            instructions="Product launch visual for Instagram"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_video_agent_returns_string():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="HOOK (0-3s): Bold text overlay...\nSCENE 1 (3-8s): Product closeup...")]

    with patch("backend.agents.video_agent._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = generate_video_content(
            brand_guidelines={"tone": "energetic", "keywords": ["fast", "results"], "avoid": []},
            content_type="reel_script",
            client_name="Fitness Brand",
            instructions="30-second reel showing workout results"
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_orchestrator_routes_ads():
    with patch("backend.agents.ads_agent._get_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Ad copy here")]
        mock_client.messages.create.return_value = mock_msg
        result = orch_generate("ads", "facebook_ad", "Brand", {})
    assert isinstance(result, str)

def test_orchestrator_routes_seo():
    with patch("backend.agents.seo_agent._get_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="SEO content")]
        mock_client.messages.create.return_value = mock_msg
        result = orch_generate("seo", "blog_post", "Brand", {})
    assert isinstance(result, str)

def test_orchestrator_routes_design():
    with patch("backend.agents.design_agent._get_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Design brief")]
        mock_client.messages.create.return_value = mock_msg
        result = orch_generate("design", "image_prompt", "Brand", {})
    assert isinstance(result, str)

def test_orchestrator_routes_video():
    with patch("backend.agents.video_agent._get_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Video script")]
        mock_client.messages.create.return_value = mock_msg
        result = orch_generate("video", "reel_script", "Brand", {})
    assert isinstance(result, str)

def test_orchestrator_raises_for_unknown():
    try:
        orch_generate("unknown_type", "x", "Brand", {})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

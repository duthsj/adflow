from unittest.mock import patch, MagicMock
from backend.services.blotato import BlotatoService

def test_schedule_post_calls_correct_endpoint():
    service = BlotatoService(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "blotato-123", "status": "scheduled"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_httpx:
        mock_httpx.return_value.__enter__.return_value.post.return_value = mock_response
        result = service.schedule_post(
            platform="instagram",
            content="Test post #test",
            scheduled_at="2026-06-01T10:00:00Z",
            media_urls=[]
        )

    assert result["id"] == "blotato-123"
    assert result["status"] == "scheduled"

def test_schedule_post_sends_correct_payload():
    service = BlotatoService(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "blotato-456", "status": "scheduled"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_httpx:
        mock_client = mock_httpx.return_value.__enter__.return_value
        mock_client.post.return_value = mock_response
        service.schedule_post(
            platform="facebook",
            content="Hello world",
            scheduled_at="2026-06-02T12:00:00Z",
            media_urls=["https://example.com/img.jpg"]
        )
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs["json"]

    assert payload["platform"] == "facebook"
    assert payload["content"] == "Hello world"
    assert payload["media"] == [{"url": "https://example.com/img.jpg"}]

def test_schedule_post_uses_bearer_auth():
    service = BlotatoService(api_key="my-secret-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "x", "status": "scheduled"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_httpx:
        mock_client = mock_httpx.return_value.__enter__.return_value
        mock_client.post.return_value = mock_response
        service.schedule_post("instagram", "content", "2026-06-01T10:00:00Z")
        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs["headers"]

    assert headers["Authorization"] == "Bearer my-secret-key"
    # verify correct endpoint
    call_url = call_kwargs.args[0]
    assert call_url.endswith("/posts/schedule")

def test_schedule_post_no_media():
    service = BlotatoService(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "blotato-789", "status": "scheduled"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_httpx:
        mock_client = mock_httpx.return_value.__enter__.return_value
        mock_client.post.return_value = mock_response
        service.schedule_post("tiktok", "content", "2026-06-01T10:00:00Z")
        payload = mock_client.post.call_args.kwargs["json"]

    assert payload["media"] == []

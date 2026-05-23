import httpx
from typing import Optional

BLOTATO_BASE_URL = "https://api.blotato.com/v1"

class BlotatoService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict) -> dict:
        with httpx.Client() as client:
            r = client.post(
                f"{BLOTATO_BASE_URL}/{endpoint}",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    def _get(self, endpoint: str) -> dict:
        with httpx.Client() as client:
            r = client.get(
                f"{BLOTATO_BASE_URL}/{endpoint}",
                headers=self.headers,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()

    def schedule_post(
        self,
        platform: str,
        content: str,
        scheduled_at: str,
        media_urls: Optional[list[str]] = None,
    ) -> dict:
        payload = {
            "platform": platform,
            "content": content,
            "scheduled_at": scheduled_at,
            "media": [{"url": u} for u in (media_urls or [])],
        }
        return self._post("posts/schedule", payload)

    def get_post_status(self, blotato_id: str) -> dict:
        return self._get(f"posts/{blotato_id}")

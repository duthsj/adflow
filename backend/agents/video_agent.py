import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

SYSTEM_PROMPT = """You are an expert video content director and scriptwriter for a marketing agency.
You write detailed video scripts, storyboards, and captions for social media and ads.
Always return ONLY the script/content — no explanations, no meta-commentary.
For reel scripts: use timestamp-based format (0-3s, 3-8s, etc.) with scene description, text overlay, and audio cue.
For storyboards: describe each shot with framing, action, text, and duration.
For captions: write the full caption with hooks, story, and CTA."""

def generate_video_content(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "engaging")
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])

    type_instructions = {
        "reel_script": "Write a 15-30 second Reel/TikTok script with timestamp markers (0-3s hook, 3-15s story, 15-25s value, 25-30s CTA). Include text overlays, scene descriptions, and suggested audio.",
        "storyboard": "Write a 6-frame storyboard. Each frame: Frame N | Shot type | Action | Text overlay | Duration.",
        "youtube_script": "Write a full YouTube video script with intro hook (30s), main content sections, and outro CTA. Include [B-ROLL] markers.",
        "caption": "Write a video caption with hook (first line), story/value in 3-5 sentences, and CTA. Add 5-10 relevant hashtags.",
        "thumbnail_brief": "Write a thumbnail design brief: main text (max 5 words), visual composition, emotion/expression, color contrast strategy.",
    }.get(content_type, f"Write a {content_type} video script for this brand.")

    user_prompt = f"""Client: {client_name}
Video content type: {content_type}
Brand tone: {tone}
Keywords/themes: {", ".join(keywords) if keywords else "none specified"}
Avoid: {", ".join(avoid) if avoid else "none specified"}
{"Instructions: " + instructions if instructions else ""}

{type_instructions}"""

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text

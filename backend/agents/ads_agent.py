import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

SYSTEM_PROMPT = """You are an expert paid advertising copywriter for a marketing agency.
You write high-converting ad copy for Meta Ads (Facebook/Instagram) and Google Ads.
Always return ONLY the ad copy — no explanations, no headers, no meta-commentary.
For A/B test requests, write two distinct variants labeled 'VERSION A:' and 'VERSION B:'.
Match the client's brand tone exactly. Keep copy concise and action-oriented."""

def generate_ads_copy(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "professional")
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])

    type_instructions = {
        "facebook_ad": "Write a Facebook/Instagram ad with headline (max 40 chars), primary text (max 125 chars), and CTA button text.",
        "google_search_ad": "Write a Google Search ad with 3 headlines (max 30 chars each) and 2 descriptions (max 90 chars each).",
        "ab_test": "Write two A/B test variants (VERSION A and VERSION B) of a Facebook ad headline and primary text.",
        "story_ad": "Write a vertical story ad script: hook (3 seconds), value prop, CTA.",
    }.get(content_type, f"Write a {content_type} ad for this brand.")

    user_prompt = f"""Client: {client_name}
Ad type: {content_type}
Brand tone: {tone}
Keywords: {", ".join(keywords) if keywords else "none specified"}
Avoid: {", ".join(avoid) if avoid else "none specified"}
{"Extra instructions: " + instructions if instructions else ""}

{type_instructions}"""

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text

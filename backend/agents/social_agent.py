import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

SYSTEM_PROMPT = """You are an expert social media copywriter for a marketing agency.
You write engaging, platform-appropriate content that matches the client's brand voice.
Always return ONLY the content text — no explanations, no headers, no meta-commentary.
Write in the language that matches the brand tone (Spanish if tone mentions it, otherwise English)."""

def generate_social_post(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "professional")
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])

    user_prompt = f"""Client: {client_name}
Content type: {content_type}
Brand tone: {tone}
Keywords to include: {", ".join(keywords) if keywords else "none specified"}
Things to avoid: {", ".join(avoid) if avoid else "none specified"}
{"Additional instructions: " + instructions if instructions else ""}

Write a {content_type} for this client's social media. Include relevant hashtags at the end."""

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text

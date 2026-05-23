import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

SYSTEM_PROMPT = """You are an expert SEO content writer and strategist for a marketing agency.
You write search-optimized content that ranks well and engages readers.
Always return ONLY the content — no explanations, no meta-commentary.
For blog posts: write full structured content with H1, H2 headings and natural keyword integration.
For meta tags: write exactly 'Title: ...' and 'Description: ...' on separate lines.
For keywords: write a comma-separated list of target keywords with search intent labels."""

def generate_seo_content(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "informative")
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])

    type_instructions = {
        "blog_post": "Write a full SEO blog post (800-1200 words) with H1 title, introduction, 3-4 H2 sections, and conclusion. Include keyword naturally.",
        "meta_tags": "Write an SEO meta title (max 60 chars) and meta description (max 160 chars) for the page described.",
        "keyword_research": "Generate 20 target keywords with search intent (informational/commercial/transactional) for the topic described.",
        "product_description": "Write an SEO product description (150-300 words) that highlights benefits and includes keywords naturally.",
    }.get(content_type, f"Write SEO {content_type} content for this brand.")

    user_prompt = f"""Client: {client_name}
Content type: {content_type}
Brand tone: {tone}
Target keywords: {", ".join(keywords) if keywords else "derive from topic"}
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

import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

SYSTEM_PROMPT = """You are an expert art director and visual designer for a marketing agency.
You create detailed image generation prompts and design briefs for graphic designers.
Always return ONLY the brief/prompt — no explanations, no meta-commentary.
For image prompts: write a detailed Midjourney/DALL-E prompt with style, lighting, composition, mood.
For design briefs: write structured sections — Concept, Color Palette, Typography, Layout, References."""

def generate_design_brief(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "modern")
    colors = brand_guidelines.get("colors", [])
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])

    type_instructions = {
        "image_prompt": "Generate a detailed image generation prompt (for Midjourney or DALL-E 3) that captures the brand essence. Format: 'PROMPT: [prompt]\nSTYLE: [style]\nCOLORS: [palette]'",
        "design_brief": "Write a structured design brief with: Concept (2-3 sentences), Color Palette (hex codes + usage), Typography (font recommendations), Layout Notes, and Visual References (describe 2 reference styles).",
        "banner_brief": "Write a design brief for a web/social media banner: dimensions, hierarchy, CTA placement, visual style.",
        "logo_brief": "Write a logo design brief: concept, symbolism, color psychology, style direction (wordmark/icon/combination), usage contexts.",
    }.get(content_type, f"Write a design brief for {content_type}.")

    user_prompt = f"""Client: {client_name}
Design type: {content_type}
Brand personality: {tone}
Brand colors: {", ".join(colors) if colors else "not specified — suggest appropriate palette"}
Brand keywords: {", ".join(keywords) if keywords else "none"}
Avoid: {", ".join(avoid) if avoid else "none specified"}
{"Instructions: " + instructions if instructions else ""}

{type_instructions}"""

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text

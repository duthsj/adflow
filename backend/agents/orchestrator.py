from ..models.project import ServiceType
from .social_agent import generate_social_post

def generate_content(
    service_type: str,
    content_type: str,
    client_name: str,
    brand_guidelines: dict,
    instructions: str = ""
) -> str:
    if service_type == ServiceType.social_media:
        return generate_social_post(
            brand_guidelines=brand_guidelines,
            content_type=content_type,
            client_name=client_name,
            instructions=instructions,
        )
    raise ValueError(f"Agent for service_type '{service_type}' not yet implemented")

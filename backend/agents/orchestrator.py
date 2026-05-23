from ..models.project import ServiceType
from .social_agent import generate_social_post
from .ads_agent import generate_ads_copy
from .seo_agent import generate_seo_content
from .design_agent import generate_design_brief
from .video_agent import generate_video_content

def generate_content(
    service_type: str,
    content_type: str,
    client_name: str,
    brand_guidelines: dict,
    instructions: str = ""
) -> str:
    kwargs = dict(
        brand_guidelines=brand_guidelines,
        content_type=content_type,
        client_name=client_name,
        instructions=instructions,
    )
    if service_type == ServiceType.social_media:
        return generate_social_post(**kwargs)
    if service_type == ServiceType.ads:
        return generate_ads_copy(**kwargs)
    if service_type == ServiceType.seo:
        return generate_seo_content(**kwargs)
    if service_type == ServiceType.design:
        return generate_design_brief(**kwargs)
    if service_type == ServiceType.video:
        return generate_video_content(**kwargs)
    raise ValueError(f"No agent for service_type '{service_type}'")

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PortalTokenCreate(BaseModel):
    project_id: Optional[int] = None
    expires_hours: int = 72  # 3 days default

class PortalTokenOut(BaseModel):
    token: str
    client_id: int
    project_id: Optional[int]
    expires_at: datetime
    portal_url: str

class PortalContentItem(BaseModel):
    id: int
    type: str
    body: str
    status: str
    ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class PortalView(BaseModel):
    client_name: str
    project_title: Optional[str]
    content_items: list[PortalContentItem]

class PortalApproveRequest(BaseModel):
    content_id: int

class PortalRejectRequest(BaseModel):
    content_id: int
    comment: Optional[str] = None

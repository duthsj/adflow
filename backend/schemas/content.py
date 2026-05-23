from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.content import ContentStatus

class GenerateContentRequest(BaseModel):
    project_id: int
    content_type: str  # post, story, reel, carousel
    instructions: Optional[str] = None

class ContentItemOut(BaseModel):
    id: int
    project_id: int
    type: str
    body: str
    status: ContentStatus
    ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class ApproveContentRequest(BaseModel):
    content_id: int

class ScheduleContentRequest(BaseModel):
    content_id: int
    platform: str
    scheduled_at: datetime

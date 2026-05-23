from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.project import ProjectStatus, ServiceType

class ProjectCreate(BaseModel):
    client_id: int
    title: str
    service_type: ServiceType
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ProjectStatus] = None
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None

class ProjectOut(BaseModel):
    id: int
    client_id: int
    title: str
    service_type: ServiceType
    status: ProjectStatus
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}

from pydantic import BaseModel
from datetime import datetime
from backend.models.workspace import WorkspacePlan, WorkspaceRole, WorkspaceSubscriptionStatus

class WorkspaceOut(BaseModel):
    id: int
    name: str
    plan: WorkspacePlan
    subscription_status: WorkspaceSubscriptionStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class WorkspaceUpdate(BaseModel):
    name: str

class MemberOut(BaseModel):
    id: int
    user_id: int
    role: WorkspaceRole
    created_at: datetime
    model_config = {"from_attributes": True}

class InviteOut(BaseModel):
    invite_token: str
    expires_at: datetime

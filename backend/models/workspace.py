from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class WorkspacePlan(str, enum.Enum):
    free = "free"
    pro = "pro"
    agency = "agency"

class WorkspaceRole(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"

class WorkspaceSubscriptionStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    trialing = "trialing"

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plan = Column(Enum(WorkspacePlan), default=WorkspacePlan.free)
    stripe_customer_id = Column(String, nullable=True, unique=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    subscription_status = Column(Enum(WorkspaceSubscriptionStatus), default=WorkspaceSubscriptionStatus.inactive)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    members = relationship("WorkspaceMember", backref="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.editor)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

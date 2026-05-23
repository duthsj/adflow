from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class ProjectStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    review = "review"
    approved = "approved"
    delivered = "delivered"

class ServiceType(str, enum.Enum):
    social_media = "social_media"
    ads = "ads"
    design = "design"
    video = "video"
    seo = "seo"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.pending)
    deadline = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    client = relationship("Client", backref="projects")

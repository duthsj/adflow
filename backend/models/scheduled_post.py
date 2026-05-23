from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class ScheduledPostStatus(str, enum.Enum):
    scheduled = "scheduled"
    published = "published"
    failed = "failed"

class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    blotato_id = Column(String, nullable=True)
    status = Column(Enum(ScheduledPostStatus), default=ScheduledPostStatus.scheduled)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = relationship("ContentItem", backref="scheduled_posts")

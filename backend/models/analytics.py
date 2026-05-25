from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

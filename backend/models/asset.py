from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    r2_key = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    size = Column(Integer, nullable=False, default=0)
    tags = Column(JSON, default=lambda: [])
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

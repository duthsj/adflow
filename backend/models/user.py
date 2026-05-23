from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from ..database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    designer = "designer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.editor)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from pydantic import BaseModel, EmailStr, field_validator
from ..models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.editor

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

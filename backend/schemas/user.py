from pydantic import BaseModel, EmailStr
from ..models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.editor

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

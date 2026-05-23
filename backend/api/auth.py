from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, Token, LoginRequest
from ..api.deps import get_current_user
from ..config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=settings.algorithm)

@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        name=data.name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(
        access_token=create_token(user.id),
        token_type="bearer",
        user=user,
    )

@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(
        access_token=create_token(user.id),
        token_type="bearer",
        user=user,
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user

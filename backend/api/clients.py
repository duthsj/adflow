import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.client import Client
from ..models.user import User
from ..models.approval_token import ApprovalToken
from ..schemas.client import ClientCreate, ClientUpdate, ClientOut
from ..schemas.portal import PortalTokenCreate, PortalTokenOut
from ..api.deps import get_current_user

router = APIRouter()

@router.post("", response_model=ClientOut)
def create_client(data: ClientCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = Client(
        name=data.name,
        industry=data.industry,
        brand_guidelines=data.brand_guidelines.model_dump(),
        social_accounts=data.social_accounts.model_dump(),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Client).filter(Client.active == True).all()

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.active == True).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    updates = data.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client

@router.post("/{client_id}/portal-token", response_model=PortalTokenOut)
def create_portal_token(
    client_id: int,
    data: PortalTokenCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(Client.id == client_id, Client.active == True).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=data.expires_hours)
    token = ApprovalToken(
        token=token_str,
        client_id=client_id,
        project_id=data.project_id,
        expires_at=expires_at,
        created_by=user.id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return PortalTokenOut(
        token=token.token,
        client_id=token.client_id,
        project_id=token.project_id,
        expires_at=token.expires_at,
        portal_url=f"/portal/{token.token}",
    )

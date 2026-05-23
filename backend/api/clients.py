from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.client import Client
from ..models.user import User
from ..schemas.client import ClientCreate, ClientUpdate, ClientOut
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
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in data.model_dump(exclude_none=True).items():
        if hasattr(value, "model_dump"):
            value = value.model_dump()
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client

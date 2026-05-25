from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.asset import Asset
from ..models.client import Client
from ..models.user import User
from ..schemas.asset import AssetOut
from ..services.r2 import r2_upload, r2_presigned_url, r2_delete
from ..api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=list[AssetOut])
def list_assets(
    client_id: int = None,
    asset_type: str = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Asset)
    if client_id is not None:
        q = q.filter(Asset.client_id == client_id)
    if asset_type is not None:
        q = q.filter(Asset.type == asset_type)
    return q.order_by(Asset.created_at.desc()).all()

@router.post("/upload", response_model=AssetOut)
def upload_asset(
    client_id: int = Form(...),
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    file_bytes = file.file.read()
    key = r2_upload(file_bytes, file.filename, file.content_type or "application/octet-stream")

    asset = Asset(
        client_id=client_id,
        filename=file.filename,
        r2_key=key,
        type=asset_type,
        size=len(file_bytes),
        tags=[],
        uploaded_by=user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/{asset_id}/url")
def get_asset_url(
    asset_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    url = r2_presigned_url(asset.r2_key)
    return {"url": url}

@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    r2_delete(asset.r2_key)
    db.delete(asset)
    db.commit()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..database import get_db
from ..models.approval_token import ApprovalToken
from ..models.content import ContentItem, ContentStatus
from ..models.project import Project
from ..schemas.portal import PortalView, PortalContentItem, PortalApproveRequest, PortalRejectRequest

router = APIRouter()

def _get_valid_token(token: str, db: Session) -> ApprovalToken:
    t = db.query(ApprovalToken).filter(
        ApprovalToken.token == token,
        ApprovalToken.active == True,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Portal link not found")
    # Handle timezone-naive datetimes from SQLite
    expires_at = t.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Portal link has expired")
    return t

@router.get("/{token}", response_model=PortalView)
def get_portal(token: str, db: Session = Depends(get_db)):
    t = _get_valid_token(token, db)
    project = db.query(Project).filter(Project.id == t.project_id).first() if t.project_id else None
    q = db.query(ContentItem).join(Project).filter(Project.client_id == t.client_id)
    if t.project_id:
        q = q.filter(ContentItem.project_id == t.project_id)
    q = q.filter(ContentItem.status.in_([ContentStatus.review, ContentStatus.approved]))
    items = q.order_by(ContentItem.created_at.desc()).all()
    return PortalView(
        client_name=project.client.name if project else "Client",
        project_title=project.title if project else None,
        content_items=[PortalContentItem.model_validate(i) for i in items],
    )

@router.post("/{token}/approve")
def portal_approve(token: str, data: PortalApproveRequest, db: Session = Depends(get_db)):
    t = _get_valid_token(token, db)
    item = db.query(ContentItem).filter(ContentItem.id == data.content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    if item.status not in (ContentStatus.review, ContentStatus.approved):
        raise HTTPException(status_code=400, detail="Content cannot be approved in its current state")
    item.status = ContentStatus.approved
    db.commit()
    return {"status": "approved"}

@router.post("/{token}/reject")
def portal_reject(token: str, data: PortalRejectRequest, db: Session = Depends(get_db)):
    t = _get_valid_token(token, db)
    item = db.query(ContentItem).filter(ContentItem.id == data.content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    if item.status not in (ContentStatus.draft, ContentStatus.review, ContentStatus.approved):
        raise HTTPException(status_code=400, detail="Content cannot be rejected in its current state")
    item.status = ContentStatus.draft
    db.commit()
    return {"status": "rejected", "comment": data.comment}

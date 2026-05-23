from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models.content import ContentItem, ContentStatus
from ..models.project import Project
from ..models.scheduled_post import ScheduledPost, ScheduledPostStatus
from ..models.user import User
from ..schemas.content import GenerateContentRequest, ContentItemOut, ApproveContentRequest, ScheduleContentRequest
from ..agents.orchestrator import generate_content
from ..api.deps import get_current_user

router = APIRouter()

@router.post("/generate", response_model=ContentItemOut)
def generate(data: GenerateContentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.query(Project).options(joinedload(Project.client)).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        body = generate_content(
            service_type=project.service_type.value,
            content_type=data.content_type,
            client_name=project.client.name,
            brand_guidelines=project.client.brand_guidelines or {},
            instructions=data.instructions or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    item = ContentItem(
        project_id=data.project_id,
        type=data.content_type,
        body=body,
        ai_generated=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=list[ContentItemOut])
def list_content(project_id: int = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(ContentItem)
    if project_id is not None:
        q = q.filter(ContentItem.project_id == project_id)
    return q.order_by(ContentItem.created_at.desc()).all()

@router.post("/approve")
def approve_content(data: ApproveContentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(ContentItem).filter(ContentItem.id == data.content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    item.status = ContentStatus.approved
    item.approved_by = user.id
    db.commit()
    return {"status": "approved"}

@router.post("/schedule")
def schedule_content(data: ScheduleContentRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.query(ContentItem).filter(ContentItem.id == data.content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    post = ScheduledPost(
        content_id=data.content_id,
        platform=data.platform,
        scheduled_at=data.scheduled_at,
    )
    db.add(post)
    item.status = ContentStatus.scheduled
    db.commit()
    db.refresh(post)
    return {"id": post.id, "platform": post.platform, "scheduled_at": post.scheduled_at, "status": post.status}

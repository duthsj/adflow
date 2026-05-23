from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.project import Project
from ..models.client import Client
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from ..api.deps import get_current_user

router = APIRouter()

@router.post("", response_model=ProjectOut)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.query(Client).filter(Client.id == data.client_id, Client.active == True).first():
        raise HTTPException(status_code=404, detail="Client not found")
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("", response_model=list[ProjectOut])
def list_projects(client_id: Optional[int] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Project)
    if client_id is not None:
        q = q.filter(Project.client_id == client_id)
    return q.order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p

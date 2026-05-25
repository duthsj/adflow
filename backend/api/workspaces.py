import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from ..models.user import User
from ..schemas.workspace import WorkspaceOut, WorkspaceUpdate, MemberOut, InviteOut
from .deps import get_current_user, get_current_workspace

router = APIRouter()

_invite_store: dict[str, dict] = {}

@router.get("/me", response_model=WorkspaceOut)
def get_my_workspace(
    workspace: Workspace = Depends(get_current_workspace),
):
    return workspace

@router.put("/me", response_model=WorkspaceOut)
def update_my_workspace(
    data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    workspace.name = data.name
    db.commit()
    db.refresh(workspace)
    return workspace

@router.get("/me/members", response_model=list[MemberOut])
def list_members(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    return db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).all()

@router.post("/me/invite", response_model=InviteOut)
def create_invite(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
    _invite_store[token] = {"workspace_id": workspace.id, "expires_at": expires_at}
    return InviteOut(invite_token=token, expires_at=expires_at)

@router.post("/accept-invite/{token}")
def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    invite = _invite_store.get(token)
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invite")
    if datetime.now(timezone.utc) > invite["expires_at"]:
        del _invite_store[token]
        raise HTTPException(status_code=410, detail="Invite expired")

    already = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == invite["workspace_id"],
        WorkspaceMember.user_id == user.id,
    ).first()
    if not already:
        member = WorkspaceMember(
            workspace_id=invite["workspace_id"],
            user_id=user.id,
            role=WorkspaceRole.editor,
        )
        db.add(member)
        db.commit()
    return {"status": "joined"}

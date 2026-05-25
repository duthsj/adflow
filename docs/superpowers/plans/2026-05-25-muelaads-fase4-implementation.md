# MuelaADS Fase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-tenant workspaces, client workspace scoping, Stripe billing, members management, and onboarding to MuelaADS v0.3.0.

**Architecture:** Each user auto-gets a workspace on register. All clients are workspace-scoped. Stripe handles billing at workspace level. `get_current_workspace` FastAPI dep resolves workspace from DB per request. Frontend adds Billing and Team pages.

**Tech Stack:** FastAPI, SQLAlchemy, stripe==10.x, Alembic (already installed), Next.js 15 App Router

---

## File Map

**New backend files:**
- `backend/models/workspace.py` — Workspace + WorkspaceMember models
- `backend/schemas/workspace.py` — Pydantic schemas
- `backend/api/workspaces.py` — workspace CRUD + invite endpoints
- `backend/api/billing.py` — Stripe checkout, webhook, portal
- `backend/services/stripe_service.py` — Stripe wrapper
- `backend/alembic/versions/001_add_workspace_id_to_clients.py` — migration

**Modified backend files:**
- `backend/models/__init__.py` — add Workspace, WorkspaceMember imports
- `backend/models/client.py` — add workspace_id FK
- `backend/api/deps.py` — add get_current_workspace dependency
- `backend/api/auth.py` — auto-create workspace on register
- `backend/api/clients.py` — scope all queries by workspace_id
- `backend/config.py` — add stripe_* settings
- `backend/main.py` — register workspaces, billing routers
- `backend/requirements.txt` — add stripe

**New test files:**
- `tests/test_workspaces.py`
- `tests/test_billing.py`

**New frontend files:**
- `frontend/app/onboarding/page.tsx`
- `frontend/app/dashboard/billing/page.tsx`
- `frontend/app/dashboard/members/page.tsx`

**Modified frontend files:**
- `frontend/components/layout/Sidebar.tsx` — add Billing, Team links + plan badge
- `frontend/app/(auth)/login/page.tsx` — redirect to /onboarding after register if needed

---

## Task 1: Workspace + WorkspaceMember Models + Auth Integration

**Files:**
- Create: `backend/models/workspace.py`
- Create: `backend/schemas/workspace.py`
- Create: `backend/api/workspaces.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/api/auth.py`
- Modify: `backend/main.py`
- Create: `tests/test_workspaces.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_workspaces.py
import pytest
from tests.conftest import *  # noqa

def register_and_login(client, email="a@b.com"):
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_register_creates_workspace(client):
    h = register_and_login(client)
    r = client.get("/workspaces/me", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] is not None
    assert data["plan"] == "free"

def test_update_workspace_name(client):
    h = register_and_login(client)
    r = client.put("/workspaces/me", json={"name": "My Agency"}, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "My Agency"

def test_workspace_members_includes_owner(client):
    h = register_and_login(client)
    r = client.get("/workspaces/me/members", headers=h)
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"

def test_invite_and_accept(client):
    h_owner = register_and_login(client, "owner@b.com")
    r = client.post("/workspaces/me/invite", headers=h_owner)
    assert r.status_code == 200
    token = r.json()["invite_token"]

    client.post("/auth/register", json={"email": "guest@b.com", "password": "pass1234", "name": "Guest"})
    h_guest = register_and_login(client, "guest@b.com")
    r = client.post(f"/workspaces/accept-invite/{token}", headers=h_guest)
    assert r.status_code == 200

    r = client.get("/workspaces/me/members", headers=h_owner)
    assert len(r.json()) == 2

def test_workspace_requires_auth(client):
    r = client.get("/workspaces/me")
    assert r.status_code == 401
```

- [ ] **Step 2: Run to verify fail**
```bash
cd /c/Users/Administrator/projects/muelaads && pytest tests/test_workspaces.py -v
```
Expected: FAIL (router not registered)

- [ ] **Step 3: Create Workspace models**

```python
# backend/models/workspace.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class WorkspacePlan(str, enum.Enum):
    free = "free"
    pro = "pro"
    agency = "agency"

class WorkspaceRole(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"

class WorkspaceSubscriptionStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    trialing = "trialing"

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plan = Column(Enum(WorkspacePlan), default=WorkspacePlan.free)
    stripe_customer_id = Column(String, nullable=True, unique=True)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    subscription_status = Column(Enum(WorkspaceSubscriptionStatus), default=WorkspaceSubscriptionStatus.inactive)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    members = relationship("WorkspaceMember", backref="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.editor)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)
```

- [ ] **Step 4: Create Workspace schemas**

```python
# backend/schemas/workspace.py
from pydantic import BaseModel
from datetime import datetime
from backend.models.workspace import WorkspacePlan, WorkspaceRole, WorkspaceSubscriptionStatus

class WorkspaceOut(BaseModel):
    id: int
    name: str
    plan: WorkspacePlan
    subscription_status: WorkspaceSubscriptionStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class WorkspaceUpdate(BaseModel):
    name: str

class MemberOut(BaseModel):
    id: int
    user_id: int
    role: WorkspaceRole
    created_at: datetime
    model_config = {"from_attributes": True}

class InviteOut(BaseModel):
    invite_token: str
    expires_at: datetime
```

- [ ] **Step 5: Create Workspaces router**

```python
# backend/api/workspaces.py
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from ..models.user import User
from ..schemas.workspace import WorkspaceOut, WorkspaceUpdate, MemberOut, InviteOut
from ..api.deps import get_current_user, get_current_workspace

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
```

- [ ] **Step 6: Add get_current_workspace to deps.py**

Add this function to `backend/api/deps.py` (after existing `get_current_user`):

```python
from ..models.workspace import Workspace, WorkspaceMember

def get_current_workspace(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == user.id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workspace found. Please create a workspace first."
        )
    workspace = db.query(Workspace).filter(Workspace.id == member.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace
```

- [ ] **Step 7: Update auth.py to auto-create workspace on register**

In `backend/api/auth.py`, add import at top:
```python
from ..models.workspace import Workspace, WorkspaceMember, WorkspaceRole
```

After `db.refresh(user)` in the `register` endpoint, add workspace creation:
```python
    db.refresh(user)
    workspace = Workspace(name=f"{data.name}'s Agency")
    db.add(workspace)
    db.flush()
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.owner)
    db.add(member)
    db.commit()
```

- [ ] **Step 8: Update models/__init__.py**

Add: `from .workspace import Workspace, WorkspaceMember, WorkspacePlan, WorkspaceRole`

- [ ] **Step 9: Register workspaces router in main.py**

Add `workspaces` to import: `from .api import auth, clients, projects, content, portal, analytics, assets, reports, workspaces`

Add: `app.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])`

- [ ] **Step 10: Run tests**
```bash
pytest tests/test_workspaces.py -v
```
Expected: 5 tests PASS

- [ ] **Step 11: Run full suite**
```bash
pytest -v 2>&1 | tail -5
```
Expected: 60+ tests PASS (existing 55 + 5 new)

- [ ] **Step 12: Commit**
```bash
git add backend/models/workspace.py backend/schemas/workspace.py backend/api/workspaces.py backend/models/__init__.py backend/api/deps.py backend/api/auth.py backend/main.py tests/test_workspaces.py
git commit -m "feat: add workspaces, workspace members, invite flow, auto-create on register"
```

---

## Task 2: Client Workspace Scoping

**Files:**
- Modify: `backend/models/client.py` — add workspace_id FK
- Modify: `backend/api/clients.py` — scope all queries by workspace
- Modify: `tests/test_clients.py` — fix helper to use workspace-aware register

- [ ] **Step 1: Read current tests/test_clients.py to understand helper pattern**

```bash
cat /c/Users/Administrator/projects/muelaads/tests/test_clients.py | head -30
```

- [ ] **Step 2: Update Client model**

```python
# backend/models/client.py
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    brand_guidelines = Column(JSON, default=lambda: {})
    social_accounts = Column(JSON, default=lambda: {})
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Note: `nullable=True` so existing tests that create clients before workspace changes still work.

- [ ] **Step 3: Update clients.py to scope by workspace**

Replace `backend/api/clients.py` content:

```python
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.client import Client
from ..models.user import User
from ..models.workspace import Workspace
from ..models.approval_token import ApprovalToken
from ..schemas.client import ClientCreate, ClientUpdate, ClientOut
from ..schemas.portal import PortalTokenCreate, PortalTokenOut
from ..api.deps import get_current_user, get_current_workspace

router = APIRouter()

@router.post("", response_model=ClientOut)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    client = Client(
        workspace_id=workspace.id,
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
def list_clients(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    return db.query(Client).filter(
        Client.workspace_id == workspace.id,
        Client.active == True,
    ).all()

@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.workspace_id == workspace.id,
        Client.active == True,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.workspace_id == workspace.id,
    ).first()
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
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.workspace_id == workspace.id,
        Client.active == True,
    ).first()
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
```

- [ ] **Step 4: Fix existing tests that create clients**

The existing tests create clients WITHOUT a workspace. Now that `get_current_workspace` is a dependency on client endpoints, and it's resolved from the user's workspace, the tests need users who have workspaces.

Since `register` now auto-creates a workspace, existing test helpers that call `POST /auth/register` will auto-get a workspace. The fix is simply: ensure tests use the register endpoint (not manual User creation). 

Check `tests/test_clients.py` and `tests/test_projects.py` helpers. If they use `client.post("/auth/register", ...)` they already get workspaces auto-created. No change needed.

If any test manually creates a `User` object without a workspace, add workspace creation in the test.

- [ ] **Step 5: Run full test suite**
```bash
cd /c/Users/Administrator/projects/muelaads && pytest -v 2>&1 | tail -15
```

Fix any failures. Common issues:
- Tests that do `client.post("/clients", ...)` will now need a user with a workspace — they already have one if they used `/auth/register`
- Analytics tests that create content via projects → clients chain should still work

- [ ] **Step 6: Commit**
```bash
git add backend/models/client.py backend/api/clients.py
git commit -m "feat: scope clients by workspace — multi-tenant isolation"
```

---

## Task 3: Stripe Billing Backend

**Files:**
- Create: `backend/services/stripe_service.py`
- Create: `backend/api/billing.py`
- Modify: `backend/config.py`
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Create: `tests/test_billing.py`

- [ ] **Step 1: Install stripe**
```bash
cd /c/Users/Administrator/projects/muelaads && pip install stripe
```

Add to `backend/requirements.txt`:
```
stripe==11.4.1
```

- [ ] **Step 2: Add Stripe settings to config.py**

Add to `Settings` class in `backend/config.py`:
```python
stripe_secret_key: str = ""
stripe_webhook_secret: str = ""
stripe_pro_price_id: str = ""
stripe_agency_price_id: str = ""
frontend_url: str = "http://localhost:3000"
```

- [ ] **Step 3: Write failing tests**

```python
# tests/test_billing.py
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import *  # noqa

def auth_header(client, email="a@b.com"):
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "A"})
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_billing_status_free(client):
    h = auth_header(client)
    r = client.get("/billing/status", headers=h)
    assert r.status_code == 200
    assert r.json()["plan"] == "free"

def test_checkout_requires_auth(client):
    r = client.post("/billing/checkout", json={"plan": "pro"})
    assert r.status_code == 401

def test_checkout_creates_session(client):
    h = auth_header(client)
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/fake"

    mock_customer = MagicMock()
    mock_customer.id = "cus_fake123"

    with patch("backend.api.billing.stripe") as mock_stripe:
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.checkout.Session.create.return_value = mock_session
        r = client.post("/billing/checkout", json={"plan": "pro"}, headers=h)

    assert r.status_code == 200
    assert r.json()["checkout_url"] == "https://checkout.stripe.com/fake"

def test_webhook_subscription_created(client):
    import json
    from backend.models.workspace import WorkspacePlan

    h = auth_header(client)
    r = client.get("/workspaces/me", headers=h)
    workspace_id = r.json()["id"]

    payload = json.dumps({
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_fake123",
                "status": "active",
                "metadata": {"workspace_id": str(workspace_id)},
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        }
    }).encode()

    with patch("backend.api.billing.stripe.Webhook.construct_event") as mock_verify:
        mock_verify.return_value = json.loads(payload)
        r = client.post(
            "/billing/webhook",
            content=payload,
            headers={"stripe-signature": "fake_sig", "content-type": "application/json"},
        )
    assert r.status_code == 200
```

- [ ] **Step 4: Run to verify fail**
```bash
pytest tests/test_billing.py -v
```
Expected: FAIL

- [ ] **Step 5: Create Stripe service**

```python
# backend/services/stripe_service.py
import stripe as stripe_lib
from ..config import settings

def get_stripe():
    stripe_lib.api_key = settings.stripe_secret_key
    return stripe_lib

def create_customer(email: str, workspace_id: int) -> str:
    s = get_stripe()
    customer = s.Customer.create(
        email=email,
        metadata={"workspace_id": str(workspace_id)},
    )
    return customer.id

def create_checkout_session(
    customer_id: str,
    price_id: str,
    workspace_id: int,
    success_url: str,
    cancel_url: str,
) -> str:
    s = get_stripe()
    session = s.checkout.Session.create(
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        subscription_data={"metadata": {"workspace_id": str(workspace_id)}},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url

def create_billing_portal(customer_id: str, return_url: str) -> str:
    s = get_stripe()
    session = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url
```

- [ ] **Step 6: Create billing router**

```python
# backend/api/billing.py
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.workspace import Workspace, WorkspacePlan, WorkspaceSubscriptionStatus
from ..models.user import User
from ..api.deps import get_current_user, get_current_workspace
from ..config import settings

router = APIRouter()

stripe.api_key = settings.stripe_secret_key

PLAN_PRICE_MAP = {
    "pro": settings.stripe_pro_price_id,
    "agency": settings.stripe_agency_price_id,
}

class CheckoutRequest(BaseModel):
    plan: str

@router.get("/status")
def billing_status(workspace: Workspace = Depends(get_current_workspace)):
    return {
        "plan": workspace.plan,
        "subscription_status": workspace.subscription_status,
        "stripe_customer_id": workspace.stripe_customer_id,
    }

@router.post("/checkout")
def create_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    if data.plan not in PLAN_PRICE_MAP:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'pro' or 'agency'.")

    price_id = PLAN_PRICE_MAP[data.plan]
    if not price_id:
        raise HTTPException(status_code=503, detail="Billing not configured")

    if not workspace.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=workspace.name,
            metadata={"workspace_id": str(workspace.id)},
        )
        workspace.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=workspace.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        subscription_data={"metadata": {"workspace_id": str(workspace.id)}},
        success_url=f"{settings.frontend_url}/dashboard/billing?success=1",
        cancel_url=f"{settings.frontend_url}/dashboard/billing?cancelled=1",
    )
    return {"checkout_url": session.url}

@router.get("/portal")
def billing_portal(
    workspace: Workspace = Depends(get_current_workspace),
):
    if not workspace.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Subscribe first.")
    session = stripe.billing_portal.Session.create(
        customer=workspace.stripe_customer_id,
        return_url=f"{settings.frontend_url}/dashboard/billing",
    )
    return {"portal_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_type = event["type"]
    sub_obj = event["data"]["object"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        workspace_id_str = sub_obj.get("metadata", {}).get("workspace_id")
        if workspace_id_str:
            workspace = db.query(Workspace).filter(Workspace.id == int(workspace_id_str)).first()
            if workspace:
                workspace.stripe_subscription_id = sub_obj["id"]
                status = sub_obj.get("status", "inactive")
                workspace.subscription_status = WorkspaceSubscriptionStatus.active if status == "active" else WorkspaceSubscriptionStatus.inactive
                price_id = sub_obj.get("items", {}).get("data", [{}])[0].get("price", {}).get("id", "")
                if price_id == settings.stripe_pro_price_id:
                    workspace.plan = WorkspacePlan.pro
                elif price_id == settings.stripe_agency_price_id:
                    workspace.plan = WorkspacePlan.agency
                db.commit()

    elif event_type == "customer.subscription.deleted":
        workspace_id_str = sub_obj.get("metadata", {}).get("workspace_id")
        if workspace_id_str:
            workspace = db.query(Workspace).filter(Workspace.id == int(workspace_id_str)).first()
            if workspace:
                workspace.plan = WorkspacePlan.free
                workspace.subscription_status = WorkspaceSubscriptionStatus.inactive
                workspace.stripe_subscription_id = None
                db.commit()

    return {"status": "ok"}
```

- [ ] **Step 7: Register billing router in main.py**

Add `billing` to import and add:
```python
app.include_router(billing.router, prefix="/billing", tags=["billing"])
```

- [ ] **Step 8: Run tests**
```bash
pytest tests/test_billing.py -v
```
Expected: 4 tests PASS

- [ ] **Step 9: Run full suite**
```bash
pytest -v 2>&1 | tail -5
```
Expected: 70+ tests PASS

- [ ] **Step 10: Commit**
```bash
git add backend/services/stripe_service.py backend/api/billing.py backend/config.py backend/main.py backend/requirements.txt tests/test_billing.py
git commit -m "feat: add Stripe billing — checkout, webhook, portal, plan management"
```

---

## Task 4: Frontend — Billing Page + Sidebar Updates

**Files:**
- Create: `frontend/app/dashboard/billing/page.tsx`
- Modify: `frontend/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create Billing page**

```tsx
// frontend/app/dashboard/billing/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { toast } from "sonner";

interface BillingStatus {
  plan: "free" | "pro" | "agency";
  subscription_status: string;
}

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "",
    features: ["2 clientes", "10 contenidos/mes", "5 agentes AI", "Portal de aprobaciones"],
    priceId: null,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    period: "/mes",
    features: ["20 clientes", "Contenido ilimitado", "5 agentes AI", "Analytics + PDF reports", "Media library"],
    priceId: "pro",
  },
  {
    id: "agency",
    name: "Agency",
    price: "$99",
    period: "/mes",
    features: ["Clientes ilimitados", "Todo en Pro", "Multi-workspace", "White label", "Soporte prioritario"],
    priceId: "agency",
  },
];

export default function BillingPage() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    api.get("/billing/status").then((r) => setStatus(r.data)).catch(() => {});

    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) toast.success("Suscripción activada. ¡Bienvenido!");
    if (params.get("cancelled")) toast.info("Pago cancelado.");
  }, []);

  const handleUpgrade = async (planId: string) => {
    setLoading(planId);
    try {
      const r = await api.post("/billing/checkout", { plan: planId });
      window.location.href = r.data.checkout_url;
    } catch {
      toast.error("Error iniciando el pago. Intenta de nuevo.");
      setLoading(null);
    }
  };

  const handlePortal = async () => {
    setLoading("portal");
    try {
      const r = await api.get("/billing/portal");
      window.location.href = r.data.portal_url;
    } catch {
      toast.error("Error abriendo el portal de facturación.");
      setLoading(null);
    }
  };

  const currentPlan = status?.plan ?? "free";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facturación</h1>
          <p className="text-sm text-gray-500 mt-1">
            Plan actual: <span className="font-medium capitalize">{currentPlan}</span>
            {status?.subscription_status === "active" && (
              <Badge className="ml-2 bg-green-100 text-green-700">Activo</Badge>
            )}
          </p>
        </div>
        {currentPlan !== "free" && (
          <Button variant="outline" onClick={handlePortal} disabled={loading === "portal"}>
            {loading === "portal" ? "Cargando..." : "Gestionar suscripción"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => {
          const isCurrent = currentPlan === plan.id;
          return (
            <Card
              key={plan.id}
              className={`relative ${isCurrent ? "ring-2 ring-orange-500" : ""} ${plan.id === "pro" ? "shadow-lg" : ""}`}
            >
              {plan.id === "pro" && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-orange-500 text-white px-3">Más popular</Badge>
                </div>
              )}
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                  {isCurrent && <Badge variant="outline" className="text-orange-600 border-orange-300">Actual</Badge>}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-gray-500 text-sm">{plan.period}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <span className="text-orange-500">✓</span> {f}
                    </li>
                  ))}
                </ul>
                {!isCurrent && plan.priceId && (
                  <Button
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                    onClick={() => handleUpgrade(plan.priceId!)}
                    disabled={loading === plan.priceId}
                  >
                    {loading === plan.priceId ? "Redirigiendo..." : `Upgrade a ${plan.name}`}
                  </Button>
                )}
                {isCurrent && (
                  <Button className="w-full" variant="outline" disabled>
                    Plan actual
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update Sidebar — add Billing + Team nav + plan badge**

Read the current Sidebar first, then replace its content:

```tsx
// frontend/components/layout/Sidebar.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, FolderKanban, Calendar, BarChart2, Image, CreditCard, UserPlus, LogOut } from "lucide-react";
import { removeToken } from "@/lib/auth";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/clients", label: "Clientes", icon: Users },
  { href: "/dashboard/projects", label: "Proyectos", icon: FolderKanban },
  { href: "/dashboard/calendar", label: "Calendario", icon: Calendar },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/dashboard/assets", label: "Assets", icon: Image },
  { href: "/dashboard/members", label: "Equipo", icon: UserPlus },
  { href: "/dashboard/billing", label: "Facturación", icon: CreditCard },
];

const PLAN_COLORS: Record<string, string> = {
  free: "bg-gray-600 text-gray-200",
  pro: "bg-orange-600 text-white",
  agency: "bg-purple-600 text-white",
};

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [plan, setPlan] = useState<string>("free");

  useEffect(() => {
    api.get("/billing/status").then((r) => setPlan(r.data.plan)).catch(() => {});
  }, []);

  const logout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold text-orange-400">MuelaADS</h1>
        <p className="text-xs text-gray-400 mt-1">Marketing Agency</p>
        <span className={cn("inline-block mt-2 text-xs px-2 py-0.5 rounded-full font-medium capitalize", PLAN_COLORS[plan] ?? PLAN_COLORS.free)}>
          {plan}
        </span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              pathname === href
                ? "bg-orange-500 text-white"
                : "text-gray-300 hover:bg-gray-800"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white w-full"
        >
          <LogOut size={18} />
          Salir
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 3: Build check**
```bash
cd /c/Users/Administrator/projects/muelaads/frontend && npm run build 2>&1 | tail -15
```

- [ ] **Step 4: Commit**
```bash
cd /c/Users/Administrator/projects/muelaads && git add frontend/app/dashboard/billing/ frontend/components/layout/Sidebar.tsx
git commit -m "feat: add billing page with plan cards, Stripe checkout, sidebar plan badge"
```

---

## Task 5: Frontend — Members Page + Onboarding

**Files:**
- Create: `frontend/app/dashboard/members/page.tsx`
- Create: `frontend/app/onboarding/page.tsx`

- [ ] **Step 1: Create Members page**

```tsx
// frontend/app/dashboard/members/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Check } from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface Member {
  id: number;
  user_id: number;
  role: string;
  created_at: string;
}

interface InviteResult {
  invite_token: string;
  expires_at: string;
}

const ROLE_COLORS: Record<string, string> = {
  owner: "bg-orange-100 text-orange-700",
  editor: "bg-blue-100 text-blue-700",
  viewer: "bg-gray-100 text-gray-700",
};

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invite, setInvite] = useState<InviteResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/workspaces/me/members").then((r) => setMembers(r.data)).catch(() => {});
  }, []);

  const createInvite = async () => {
    setLoading(true);
    try {
      const r = await api.post("/workspaces/me/invite");
      setInvite(r.data);
    } catch {
      toast.error("Error generando invitación");
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    if (!invite) return;
    const url = `${window.location.origin}/join/${invite.invite_token}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success("Link copiado");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Equipo</h1>
        <Button onClick={createInvite} disabled={loading}>
          {loading ? "Generando..." : "Invitar miembro"}
        </Button>
      </div>

      {invite && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-4">
            <p className="text-sm font-medium text-orange-800 mb-2">Link de invitación (expira en 48h):</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs bg-white border rounded p-2 text-gray-700 truncate">
                {`${window.location.origin}/join/${invite.invite_token}`}
              </code>
              <Button size="sm" variant="outline" onClick={copyLink}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Miembros ({members.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {members.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">Sin miembros todavía</p>
          ) : (
            <div className="divide-y">
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Usuario #{m.user_id}</p>
                    <p className="text-xs text-gray-400">
                      Desde {new Date(m.created_at).toLocaleDateString("es")}
                    </p>
                  </div>
                  <Badge className={ROLE_COLORS[m.role] ?? "bg-gray-100"}>{m.role}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Create Onboarding page**

```tsx
// frontend/app/onboarding/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";
import { toast } from "sonner";

export default function OnboardingPage() {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.put("/workspaces/me", { name: name.trim() });
      toast.success("Workspace configurado");
      router.push("/dashboard");
    } catch {
      toast.error("Error configurando workspace");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <h1 className="text-2xl font-bold text-orange-500">MuelaADS</h1>
          <CardTitle className="text-lg mt-2">¡Bienvenido! Configura tu agencia</CardTitle>
          <p className="text-sm text-gray-500">Dale un nombre a tu workspace para comenzar</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de tu agencia</Label>
              <Input
                id="name"
                placeholder="Ej: Agencia Creativa XYZ"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-orange-500 hover:bg-orange-600 text-white"
              disabled={loading || !name.trim()}
            >
              {loading ? "Configurando..." : "Comenzar →"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: Build check**
```bash
cd /c/Users/Administrator/projects/muelaads/frontend && npm run build 2>&1 | tail -15
```

- [ ] **Step 4: Commit**
```bash
cd /c/Users/Administrator/projects/muelaads && git add frontend/app/dashboard/members/ frontend/app/onboarding/
git commit -m "feat: add members management page and onboarding workspace setup"
```

---

## Task 6: Final Tests + Tag v0.4.0

- [ ] **Step 1: Run full test suite**
```bash
cd /c/Users/Administrator/projects/muelaads && pytest -v 2>&1 | tail -15
```
Expected: 70+ tests PASS

- [ ] **Step 2: Frontend build**
```bash
cd /c/Users/Administrator/projects/muelaads/frontend && npm run build 2>&1 | tail -5
```
Expected: clean

- [ ] **Step 3: Tag**
```bash
cd /c/Users/Administrator/projects/muelaads && git tag v0.4.0 && git push origin main && git push origin v0.4.0
```

- [ ] **Step 4: Commit spec**
```bash
git add docs/superpowers/specs/2026-05-25-muelaads-fase4-design.md docs/superpowers/plans/2026-05-25-muelaads-fase4-implementation.md
git commit -m "docs: add Fase 4 spec and implementation plan"
```

---

## Self-Review

**Spec coverage:**
- ✅ Workspace model + CRUD — Task 1
- ✅ WorkspaceMember + roles — Task 1
- ✅ Invite flow (token-based) — Task 1
- ✅ Auto-create workspace on register — Task 1
- ✅ get_current_workspace dep — Task 1
- ✅ Client workspace scoping — Task 2
- ✅ Stripe checkout + webhook + portal — Task 3
- ✅ Plan management (free/pro/agency) — Task 3
- ✅ Billing page + plan cards — Task 4
- ✅ Sidebar plan badge — Task 4
- ✅ Members page — Task 5
- ✅ Onboarding page — Task 5

**Type consistency:**
- `WorkspacePlan`, `WorkspaceRole`, `WorkspaceSubscriptionStatus` defined in `workspace.py`, imported in `billing.py` and `workspaces.py`
- `get_current_workspace` defined in `deps.py`, used in `workspaces.py`, `clients.py`, `billing.py`
- `Workspace` model used consistently

**Note on invite store:** `_invite_store` is an in-memory dict in `workspaces.py`. This is intentional for simplicity (Fase 5 could move to DB-backed invites). Works for single-process deployment (PM2 single instance).

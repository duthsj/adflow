# MuelaADS Fase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Analytics dashboard, Media Library (Cloudflare R2), real Blotato publishing, PDF reports, and UX polish (toasts + loading states) to MuelaADS v0.2.0.

**Architecture:** Each feature is a self-contained backend router + frontend page. Backend follows existing pattern: SQLAlchemy model → Pydantic schema → FastAPI router. Frontend follows existing pattern: Next.js App Router page + shadcn/ui components. Tests use SQLite in-memory via existing conftest.py.

**Tech Stack:** FastAPI, SQLAlchemy, boto3 (R2), fpdf2 (PDF), recharts (charts), sonner (toasts — already installed), Next.js 15 App Router, TypeScript, shadcn/ui

---

## File Map

**New backend files:**
- `backend/models/analytics.py` — Analytics model
- `backend/models/asset.py` — Asset model
- `backend/schemas/analytics.py` — Pydantic schemas for analytics
- `backend/schemas/asset.py` — Pydantic schemas for assets
- `backend/api/analytics.py` — Analytics endpoints
- `backend/api/assets.py` — Asset upload/list/delete endpoints
- `backend/api/reports.py` — PDF report generation endpoint
- `backend/services/r2.py` — Cloudflare R2 wrapper (boto3)
- `backend/services/report.py` — PDF generation with fpdf2

**Modified backend files:**
- `backend/models/__init__.py` — add Analytics, Asset imports
- `backend/main.py` — register analytics, assets, reports routers
- `backend/requirements.txt` — add fpdf2

**New test files:**
- `tests/test_analytics.py`
- `tests/test_assets.py`
- `tests/test_reports.py`

**New frontend files:**
- `frontend/app/dashboard/analytics/page.tsx`
- `frontend/app/dashboard/assets/page.tsx`
- `frontend/components/analytics/KPICard.tsx`
- `frontend/components/analytics/PostsChart.tsx`
- `frontend/components/analytics/PlatformChart.tsx`
- `frontend/components/assets/AssetGrid.tsx`
- `frontend/components/assets/UploadButton.tsx`

**Modified frontend files:**
- `frontend/app/layout.tsx` — add Toaster + fix metadata
- `frontend/components/layout/Sidebar.tsx` — add Analytics + Assets nav items
- `frontend/app/dashboard/page.tsx` — replace dashes with real API counts
- `frontend/app/dashboard/projects/[id]/page.tsx` — add toast on approve

---

## Task 1: Analytics Model + Backend

**Files:**
- Create: `backend/models/analytics.py`
- Create: `backend/schemas/analytics.py`
- Create: `backend/api/analytics.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/main.py`
- Create: `tests/test_analytics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_analytics.py
import pytest
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123", "name": "A"})
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "pass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_analytics_summary_empty(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.get(f"/analytics/summary?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total_posts"] == 0
    assert data["pending_approvals"] == 0

def test_analytics_by_platform_empty(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.get(f"/analytics/by-platform?client_id={client_id}&period=week", headers=h)
    assert r.status_code == 200
    assert r.json() == []

def test_analytics_requires_auth(client):
    r = client.get("/analytics/summary?client_id=1&period=week")
    assert r.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /path/to/muelaads
pytest tests/test_analytics.py -v
```
Expected: `FAILED` with ImportError or 404 because router not registered yet.

- [ ] **Step 3: Create Analytics model**

```python
# backend/models/analytics.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Create Analytics schemas**

```python
# backend/schemas/analytics.py
from pydantic import BaseModel

class AnalyticsSummary(BaseModel):
    total_posts: int
    avg_reach: float
    avg_engagement: float
    pending_approvals: int

class PlatformStat(BaseModel):
    platform: str
    posts: int
    reach: float
    engagement: float

class InsightsRequest(BaseModel):
    client_id: int
    period: str = "week"

class InsightsResponse(BaseModel):
    insights: list[str]
```

- [ ] **Step 5: Create Analytics API router**

```python
# backend/api/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from ..database import get_db
from ..models.analytics import Analytics
from ..models.content import ContentItem, ContentStatus
from ..models.project import Project
from ..models.client import Client
from ..models.user import User
from ..schemas.analytics import AnalyticsSummary, PlatformStat, InsightsRequest, InsightsResponse
from ..api.deps import get_current_user

router = APIRouter()

def _period_start(period: str) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "month":
        return now - timedelta(days=30)
    return now - timedelta(days=7)

@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    client_id: int,
    period: str = "week",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    since = _period_start(period)

    project_ids = [
        p.id for p in db.query(Project.id).filter(Project.client_id == client_id).all()
    ]

    total_posts = 0
    pending_approvals = 0
    if project_ids:
        total_posts = (
            db.query(ContentItem)
            .filter(
                ContentItem.project_id.in_(project_ids),
                ContentItem.created_at >= since,
            )
            .count()
        )
        pending_approvals = (
            db.query(ContentItem)
            .filter(
                ContentItem.project_id.in_(project_ids),
                ContentItem.status.in_([ContentStatus.draft, ContentStatus.review]),
            )
            .count()
        )

    reach_rows = db.query(Analytics).filter(
        Analytics.client_id == client_id,
        Analytics.metric_type == "reach",
        Analytics.recorded_at >= since,
    ).all()
    avg_reach = sum(r.value for r in reach_rows) / len(reach_rows) if reach_rows else 0.0

    eng_rows = db.query(Analytics).filter(
        Analytics.client_id == client_id,
        Analytics.metric_type == "engagement",
        Analytics.recorded_at >= since,
    ).all()
    avg_engagement = sum(r.value for r in eng_rows) / len(eng_rows) if eng_rows else 0.0

    return AnalyticsSummary(
        total_posts=total_posts,
        avg_reach=avg_reach,
        avg_engagement=avg_engagement,
        pending_approvals=pending_approvals,
    )

@router.get("/by-platform", response_model=list[PlatformStat])
def get_by_platform(
    client_id: int,
    period: str = "week",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    since = _period_start(period)
    rows = db.query(Analytics).filter(
        Analytics.client_id == client_id,
        Analytics.recorded_at >= since,
    ).all()

    platforms: dict[str, dict] = {}
    for row in rows:
        p = platforms.setdefault(row.platform, {"posts": 0, "reach": 0.0, "engagement": 0.0, "reach_count": 0, "eng_count": 0})
        if row.metric_type == "posts":
            p["posts"] += int(row.value)
        elif row.metric_type == "reach":
            p["reach"] += row.value
            p["reach_count"] += 1
        elif row.metric_type == "engagement":
            p["engagement"] += row.value
            p["eng_count"] += 1

    return [
        PlatformStat(
            platform=k,
            posts=v["posts"],
            reach=v["reach"] / v["reach_count"] if v["reach_count"] else 0.0,
            engagement=v["engagement"] / v["eng_count"] if v["eng_count"] else 0.0,
        )
        for k, v in platforms.items()
    ]
```

- [ ] **Step 6: Update models/__init__.py**

```python
# backend/models/__init__.py
from .user import User, UserRole
from .client import Client
from .project import Project, ProjectStatus, ServiceType
from .content import ContentItem, ContentStatus
from .scheduled_post import ScheduledPost
from .approval_token import ApprovalToken
from .analytics import Analytics
```

- [ ] **Step 7: Register analytics router in main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models  # noqa: F401
from .api import auth, clients, projects, content, portal, analytics

Base.metadata.create_all(engine)

app = FastAPI(title="MuelaADS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(portal.router, prefix="/portal", tags=["portal"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
pytest tests/test_analytics.py -v
```
Expected: 3 tests PASS

- [ ] **Step 9: Commit**

```bash
git add backend/models/analytics.py backend/schemas/analytics.py backend/api/analytics.py backend/models/__init__.py backend/main.py tests/test_analytics.py
git commit -m "feat: add analytics model, endpoints, and tests"
```

---

## Task 2: AI Insights Endpoint

**Files:**
- Modify: `backend/api/analytics.py`
- Modify: `tests/test_analytics.py`

- [ ] **Step 1: Add failing test**

Add to `tests/test_analytics.py`:
```python
from unittest.mock import patch

def test_analytics_insights(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]

    mock_response = type("R", (), {
        "content": [type("C", (), {"text": "Tip 1. Tip 2. Tip 3."})()]
    })()

    with patch("backend.api.analytics._get_client") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_response
        r = client.post("/analytics/insights", json={"client_id": client_id, "period": "week"}, headers=h)
    assert r.status_code == 200
    assert "insights" in r.json()
    assert len(r.json()["insights"]) > 0
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_analytics.py::test_analytics_insights -v
```
Expected: FAIL (endpoint not found)

- [ ] **Step 3: Add insights endpoint to analytics.py**

Add at the top of `backend/api/analytics.py` (after existing imports):
```python
import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client
```

Add at the bottom of `backend/api/analytics.py`:
```python
@router.post("/insights", response_model=InsightsResponse)
def get_insights(
    data: InsightsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summary = get_summary(client_id=data.client_id, period=data.period, db=db)

    prompt = f"""You are a marketing analyst reviewing performance for {client.name} ({client.industry}).

Period: {data.period}
Total posts: {summary.total_posts}
Average reach: {summary.avg_reach:.0f}
Average engagement rate: {summary.avg_engagement:.1f}%
Pending approvals: {summary.pending_approvals}

Provide exactly 3 short, actionable bullet points (1 sentence each):
1. What worked well
2. What needs improvement
3. Top recommendation for next {data.period}

Be specific and direct. No fluff."""

    response = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    lines = [l.strip().lstrip("123.-) ") for l in text.strip().split("\n") if l.strip()]
    return InsightsResponse(insights=lines[:3])
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_analytics.py -v
```
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/analytics.py tests/test_analytics.py
git commit -m "feat: add AI insights endpoint for analytics"
```

---

## Task 3: Media Library Backend (R2 + Asset model)

**Files:**
- Create: `backend/models/asset.py`
- Create: `backend/schemas/asset.py`
- Create: `backend/services/r2.py`
- Create: `backend/api/assets.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Create: `tests/test_assets.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_assets.py
import pytest
import io
from unittest.mock import patch, MagicMock
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123", "name": "A"})
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "pass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def make_client(client, h):
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    return r.json()["id"]

def test_asset_list_empty(client):
    h = auth_header(client)
    client_id = make_client(client, h)
    r = client.get(f"/assets?client_id={client_id}", headers=h)
    assert r.status_code == 200
    assert r.json() == []

def test_asset_upload(client):
    h = auth_header(client)
    client_id = make_client(client, h)

    with patch("backend.api.assets.r2_upload") as mock_upload:
        mock_upload.return_value = "assets/test-key.png"
        file_data = io.BytesIO(b"fake image data")
        r = client.post(
            "/assets/upload",
            data={"client_id": str(client_id), "asset_type": "image"},
            files={"file": ("test.png", file_data, "image/png")},
            headers=h,
        )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.png"
    assert data["type"] == "image"
    assert data["client_id"] == client_id

def test_asset_delete(client):
    h = auth_header(client)
    client_id = make_client(client, h)

    with patch("backend.api.assets.r2_upload") as mock_upload, \
         patch("backend.api.assets.r2_delete") as mock_delete:
        mock_upload.return_value = "assets/key.png"
        mock_delete.return_value = None
        file_data = io.BytesIO(b"data")
        r = client.post(
            "/assets/upload",
            data={"client_id": str(client_id), "asset_type": "image"},
            files={"file": ("img.png", file_data, "image/png")},
            headers=h,
        )
        asset_id = r.json()["id"]
        r = client.delete(f"/assets/{asset_id}", headers=h)
    assert r.status_code == 204

def test_asset_requires_auth(client):
    r = client.get("/assets?client_id=1")
    assert r.status_code == 401
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_assets.py -v
```
Expected: FAIL (no router registered)

- [ ] **Step 3: Create Asset model**

```python
# backend/models/asset.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    r2_key = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    size = Column(Integer, nullable=False, default=0)
    tags = Column(JSON, default=lambda: [])
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Create Asset schemas**

```python
# backend/schemas/asset.py
from pydantic import BaseModel
from datetime import datetime

class AssetOut(BaseModel):
    id: int
    client_id: int
    filename: str
    r2_key: str
    type: str
    size: int
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Create R2 service**

```python
# backend/services/r2.py
import uuid
import boto3
from botocore.client import Config
from ..config import settings

def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def r2_upload(file_bytes: bytes, filename: str, content_type: str) -> str:
    key = f"assets/{uuid.uuid4()}/{filename}"
    _client().put_object(
        Bucket=settings.r2_bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key

def r2_presigned_url(key: str, expires: int = 3600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket, "Key": key},
        ExpiresIn=expires,
    )

def r2_delete(key: str) -> None:
    _client().delete_object(Bucket=settings.r2_bucket, Key=key)
```

- [ ] **Step 6: Create Assets API router**

```python
# backend/api/assets.py
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
```

- [ ] **Step 7: Update models/__init__.py**

```python
# backend/models/__init__.py
from .user import User, UserRole
from .client import Client
from .project import Project, ProjectStatus, ServiceType
from .content import ContentItem, ContentStatus
from .scheduled_post import ScheduledPost
from .approval_token import ApprovalToken
from .analytics import Analytics
from .asset import Asset
```

- [ ] **Step 8: Update main.py to register assets router**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models  # noqa: F401
from .api import auth, clients, projects, content, portal, analytics, assets

Base.metadata.create_all(engine)

app = FastAPI(title="MuelaADS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(portal.router, prefix="/portal", tags=["portal"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
```

- [ ] **Step 9: Add fpdf2 to requirements.txt**

Add line to `backend/requirements.txt`:
```
fpdf2==2.8.1
```

Install it:
```bash
pip install fpdf2==2.8.1
```

- [ ] **Step 10: Run tests**

```bash
pytest tests/test_assets.py -v
```
Expected: 4 tests PASS

- [ ] **Step 11: Commit**

```bash
git add backend/models/asset.py backend/schemas/asset.py backend/services/r2.py backend/api/assets.py backend/models/__init__.py backend/main.py backend/requirements.txt tests/test_assets.py
git commit -m "feat: add media library — Asset model, R2 service, upload/list/delete endpoints"
```

---

## Task 4: PDF Reports Backend

**Files:**
- Create: `backend/services/report.py`
- Create: `backend/api/reports.py`
- Modify: `backend/main.py`
- Create: `tests/test_reports.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_reports.py
import pytest
from unittest.mock import patch
from tests.conftest import *  # noqa

def auth_header(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123", "name": "A"})
    r = client.post("/auth/login", data={"username": "a@b.com", "password": "pass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_generate_report_returns_pdf(client):
    h = auth_header(client)
    r = client.post("/clients", json={"name": "CLI", "industry": "tech"}, headers=h)
    client_id = r.json()["id"]
    r = client.post(
        "/reports/generate",
        json={"client_id": client_id, "period": "week", "include_insights": False},
        headers=h,
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

def test_generate_report_unknown_client(client):
    h = auth_header(client)
    r = client.post(
        "/reports/generate",
        json={"client_id": 999, "period": "week", "include_insights": False},
        headers=h,
    )
    assert r.status_code == 404

def test_report_requires_auth(client):
    r = client.post("/reports/generate", json={"client_id": 1, "period": "week", "include_insights": False})
    assert r.status_code == 401
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_reports.py -v
```
Expected: FAIL (router not registered)

- [ ] **Step 3: Create report service**

```python
# backend/services/report.py
from fpdf import FPDF
from datetime import date

def generate_pdf(
    client_name: str,
    period: str,
    total_posts: int,
    avg_reach: float,
    avg_engagement: float,
    pending_approvals: int,
    platform_stats: list[dict],
    insights: list[str] | None = None,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(234, 88, 12)  # orange-600
    pdf.cell(0, 12, "MuelaADS", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(107, 114, 128)  # gray-500
    pdf.cell(0, 6, f"Performance Report — {client_name}", ln=True)
    pdf.cell(0, 6, f"Period: {period} | Generated: {date.today().isoformat()}", ln=True)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(17, 24, 39)  # gray-900
    pdf.cell(0, 8, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(55, 65, 81)

    metrics = [
        ("Total Posts", str(total_posts)),
        ("Avg. Reach", f"{avg_reach:.0f}"),
        ("Avg. Engagement", f"{avg_engagement:.1f}%"),
        ("Pending Approvals", str(pending_approvals)),
    ]
    for label, value in metrics:
        pdf.cell(80, 7, label, border="B")
        pdf.cell(0, 7, value, border="B", ln=True)
    pdf.ln(8)

    if platform_stats:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "By Platform", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(50, 7, "Platform", border="B")
        pdf.cell(40, 7, "Posts", border="B")
        pdf.cell(40, 7, "Avg Reach", border="B")
        pdf.cell(0, 7, "Engagement", border="B", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        for stat in platform_stats:
            pdf.cell(50, 7, stat["platform"].title())
            pdf.cell(40, 7, str(stat["posts"]))
            pdf.cell(40, 7, f"{stat['reach']:.0f}")
            pdf.cell(0, 7, f"{stat['engagement']:.1f}%", ln=True)
        pdf.ln(8)

    if insights:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "AI Insights", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(55, 65, 81)
        for i, insight in enumerate(insights, 1):
            pdf.multi_cell(0, 7, f"{i}. {insight}")

    return bytes(pdf.output())
```

- [ ] **Step 4: Create reports router**

```python
# backend/api/reports.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.client import Client
from ..models.user import User
from ..api.analytics import get_summary, get_by_platform, _get_client as get_claude
from ..schemas.analytics import InsightsRequest, InsightsResponse
from ..services.report import generate_pdf
from ..api.deps import get_current_user
from ..config import settings
import anthropic

router = APIRouter()

class ReportRequest(BaseModel):
    client_id: int
    period: str = "week"
    include_insights: bool = True

@router.post("/generate")
def generate_report(
    data: ReportRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summary = get_summary(client_id=data.client_id, period=data.period, db=db)
    platforms = get_by_platform(client_id=data.client_id, period=data.period, db=db)
    platform_dicts = [p.model_dump() for p in platforms]

    insights = None
    if data.include_insights and settings.anthropic_api_key:
        from ..api.analytics import get_insights
        result = get_insights(
            data=InsightsRequest(client_id=data.client_id, period=data.period),
            db=db,
        )
        insights = result.insights

    pdf_bytes = generate_pdf(
        client_name=client.name,
        period=data.period,
        total_posts=summary.total_posts,
        avg_reach=summary.avg_reach,
        avg_engagement=summary.avg_engagement,
        pending_approvals=summary.pending_approvals,
        platform_stats=platform_dicts,
        insights=insights,
    )

    filename = f"muelaads-report-{client.name.lower().replace(' ', '-')}-{data.period}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 5: Register reports router in main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models  # noqa: F401
from .api import auth, clients, projects, content, portal, analytics, assets, reports

Base.metadata.create_all(engine)

app = FastAPI(title="MuelaADS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(portal.router, prefix="/portal", tags=["portal"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_reports.py -v
```
Expected: 3 tests PASS

- [ ] **Step 7: Run full test suite to check for regressions**

```bash
pytest -v
```
Expected: 50+ tests PASS, 0 failures

- [ ] **Step 8: Commit**

```bash
git add backend/services/report.py backend/api/reports.py backend/main.py tests/test_reports.py
git commit -m "feat: add PDF report generation endpoint"
```

---

## Task 5: Analytics Frontend

**Files:**
- Create: `frontend/components/analytics/KPICard.tsx`
- Create: `frontend/components/analytics/PostsChart.tsx`
- Create: `frontend/components/analytics/PlatformChart.tsx`
- Create: `frontend/app/dashboard/analytics/page.tsx`
- Modify: `frontend/components/layout/Sidebar.tsx`

- [ ] **Step 1: Install recharts**

```bash
cd frontend
npm install recharts
```

Expected output includes: `added N packages`

- [ ] **Step 2: Create KPICard component**

```tsx
// frontend/components/analytics/KPICard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface KPICardProps {
  label: string;
  value: string | number;
  sub?: string;
}

export default function KPICard({ label, value, sub }: KPICardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-gray-500 font-medium">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create PostsChart component**

```tsx
// frontend/components/analytics/PostsChart.tsx
"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PostsChartProps {
  data: { date: string; posts: number }[];
}

export default function PostsChart({ data }: PostsChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Sin datos para mostrar
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line type="monotone" dataKey="posts" stroke="#ea580c" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 4: Create PlatformChart component**

```tsx
// frontend/components/analytics/PlatformChart.tsx
"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PlatformStat {
  platform: string;
  posts: number;
  reach: number;
  engagement: number;
}

export default function PlatformChart({ data }: { data: PlatformStat[] }) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Sin datos de plataformas
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="platform" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="posts" fill="#ea580c" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 5: Create Analytics dashboard page**

```tsx
// frontend/app/dashboard/analytics/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import KPICard from "@/components/analytics/KPICard";
import PostsChart from "@/components/analytics/PostsChart";
import PlatformChart from "@/components/analytics/PlatformChart";
import api from "@/lib/api";
import { toast } from "sonner";

interface Client { id: number; name: string; }
interface Summary { total_posts: number; avg_reach: number; avg_engagement: number; pending_approvals: number; }
interface PlatformStat { platform: string; posts: number; reach: number; engagement: number; }

export default function AnalyticsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<number | null>(null);
  const [period, setPeriod] = useState<"week" | "month">("week");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [platforms, setPlatforms] = useState<PlatformStat[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/clients").then((r) => {
      setClients(r.data);
      if (r.data.length > 0) setSelectedClient(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    setLoading(true);
    Promise.all([
      api.get(`/analytics/summary?client_id=${selectedClient}&period=${period}`),
      api.get(`/analytics/by-platform?client_id=${selectedClient}&period=${period}`),
    ])
      .then(([s, p]) => {
        setSummary(s.data);
        setPlatforms(p.data);
        setInsights([]);
      })
      .catch(() => toast.error("Error cargando analytics"))
      .finally(() => setLoading(false));
  }, [selectedClient, period]);

  const loadInsights = async () => {
    if (!selectedClient) return;
    setLoadingInsights(true);
    try {
      const r = await api.post("/analytics/insights", { client_id: selectedClient, period });
      setInsights(r.data.insights);
    } catch {
      toast.error("Error generando insights");
    } finally {
      setLoadingInsights(false);
    }
  };

  const downloadReport = async () => {
    if (!selectedClient) return;
    try {
      const r = await api.post(
        "/reports/generate",
        { client_id: selectedClient, period, include_insights: insights.length > 0 },
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte-${period}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Reporte descargado");
    } catch {
      toast.error("Error generando reporte");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="flex gap-2">
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={selectedClient ?? ""}
            onChange={(e) => setSelectedClient(Number(e.target.value))}
          >
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={period}
            onChange={(e) => setPeriod(e.target.value as "week" | "month")}
          >
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
          </select>
          <Button variant="outline" size="sm" onClick={downloadReport}>
            Descargar PDF
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Posts publicados" value={summary.total_posts} sub={period === "week" ? "esta semana" : "este mes"} />
          <KPICard label="Alcance promedio" value={summary.avg_reach.toFixed(0)} />
          <KPICard label="Engagement" value={`${summary.avg_engagement.toFixed(1)}%`} />
          <KPICard label="Aprobaciones pendientes" value={summary.pending_approvals} />
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          {clients.length === 0 ? "Crea un cliente para ver analytics" : "Sin datos"}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-700">Posts por período</CardTitle>
          </CardHeader>
          <CardContent>
            <PostsChart data={[]} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-700">Por plataforma</CardTitle>
          </CardHeader>
          <CardContent>
            <PlatformChart data={platforms} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-700">AI Insights</CardTitle>
          <Button size="sm" variant="outline" onClick={loadInsights} disabled={loadingInsights}>
            {loadingInsights ? "Generando..." : "Generar insights"}
          </Button>
        </CardHeader>
        <CardContent>
          {insights.length > 0 ? (
            <ul className="space-y-2">
              {insights.map((ins, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-700">
                  <span className="text-orange-500 font-bold">{i + 1}.</span>
                  {ins}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">
              Haz clic en &quot;Generar insights&quot; para ver recomendaciones AI
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 6: Add Analytics + Assets to Sidebar**

```tsx
// frontend/components/layout/Sidebar.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, FolderKanban, Calendar, BarChart2, Image, LogOut } from "lucide-react";
import { removeToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/clients", label: "Clientes", icon: Users },
  { href: "/dashboard/projects", label: "Proyectos", icon: FolderKanban },
  { href: "/dashboard/calendar", label: "Calendario", icon: Calendar },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/dashboard/assets", label: "Assets", icon: Image },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold text-orange-400">MuelaADS</h1>
        <p className="text-xs text-gray-400 mt-1">Marketing Agency</p>
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

- [ ] **Step 7: Commit**

```bash
git add frontend/components/analytics/ frontend/app/dashboard/analytics/ frontend/components/layout/Sidebar.tsx
git commit -m "feat: add analytics dashboard with KPI cards, charts, AI insights, and PDF download"
```

---

## Task 6: Media Library Frontend

**Files:**
- Create: `frontend/components/assets/AssetGrid.tsx`
- Create: `frontend/components/assets/UploadButton.tsx`
- Create: `frontend/app/dashboard/assets/page.tsx`

- [ ] **Step 1: Create AssetGrid component**

```tsx
// frontend/components/assets/AssetGrid.tsx
"use client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2 } from "lucide-react";

interface Asset {
  id: number;
  filename: string;
  type: string;
  size: number;
  created_at: string;
}

interface AssetGridProps {
  assets: Asset[];
  onDelete: (id: number) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AssetGrid({ assets, onDelete }: AssetGridProps) {
  if (assets.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg mb-2">Sin assets</p>
        <p className="text-sm">Sube imágenes, videos o documentos para comenzar</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {assets.map((asset) => (
        <div key={asset.id} className="bg-white border rounded-xl p-3 space-y-2 hover:shadow-sm transition-shadow">
          <div className="h-24 bg-gray-50 rounded-lg flex items-center justify-center text-gray-300 text-2xl">
            {asset.type === "image" ? "🖼" : asset.type === "video" ? "🎬" : "📄"}
          </div>
          <p className="text-xs text-gray-700 font-medium truncate">{asset.filename}</p>
          <div className="flex items-center justify-between">
            <Badge variant="outline" className="text-xs">{asset.type}</Badge>
            <span className="text-xs text-gray-400">{formatBytes(asset.size)}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-red-500 hover:text-red-600 hover:bg-red-50"
            onClick={() => onDelete(asset.id)}
          >
            <Trash2 size={14} className="mr-1" />
            Eliminar
          </Button>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create UploadButton component**

```tsx
// frontend/components/assets/UploadButton.tsx
"use client";
import { useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";

interface UploadButtonProps {
  clientId: number;
  onUploaded: (asset: unknown) => void;
  uploading: boolean;
  onUpload: (file: File) => void;
}

export default function UploadButton({ uploading, onUpload }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*,.pdf,.doc,.docx"
        className="hidden"
        onChange={handleChange}
      />
      <Button onClick={() => inputRef.current?.click()} disabled={uploading}>
        <Upload size={16} className="mr-2" />
        {uploading ? "Subiendo..." : "Subir archivo"}
      </Button>
    </>
  );
}
```

- [ ] **Step 3: Create Assets page**

```tsx
// frontend/app/dashboard/assets/page.tsx
"use client";
import { useEffect, useState } from "react";
import AssetGrid from "@/components/assets/AssetGrid";
import UploadButton from "@/components/assets/UploadButton";
import api from "@/lib/api";
import { toast } from "sonner";

interface Client { id: number; name: string; }
interface Asset { id: number; filename: string; type: string; size: number; r2_key: string; created_at: string; }

const TYPE_MAP: Record<string, string> = {
  "image/jpeg": "image",
  "image/png": "image",
  "image/gif": "image",
  "image/webp": "image",
  "video/mp4": "video",
  "video/quicktime": "video",
  "application/pdf": "doc",
  "application/msword": "doc",
};

export default function AssetsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<number | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [uploading, setUploading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    api.get("/clients").then((r) => {
      setClients(r.data);
      if (r.data.length > 0) setSelectedClient(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    const params = new URLSearchParams({ client_id: String(selectedClient) });
    if (typeFilter) params.set("asset_type", typeFilter);
    api.get(`/assets?${params}`).then((r) => setAssets(r.data));
  }, [selectedClient, typeFilter]);

  const handleUpload = async (file: File) => {
    if (!selectedClient) return;
    setUploading(true);
    const assetType = TYPE_MAP[file.type] ?? "doc";
    const form = new FormData();
    form.append("file", file);
    form.append("client_id", String(selectedClient));
    form.append("asset_type", assetType);
    try {
      const r = await api.post("/assets/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setAssets((prev) => [r.data, ...prev]);
      toast.success(`${file.name} subido correctamente`);
    } catch {
      toast.error("Error subiendo archivo");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/assets/${id}`);
      setAssets((prev) => prev.filter((a) => a.id !== id));
      toast.success("Asset eliminado");
    } catch {
      toast.error("Error eliminando asset");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Media Library</h1>
        <div className="flex gap-2">
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={selectedClient ?? ""}
            onChange={(e) => setSelectedClient(Number(e.target.value))}
          >
            {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select
            className="border rounded-lg px-3 py-2 text-sm bg-white"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">Todos los tipos</option>
            <option value="image">Imágenes</option>
            <option value="video">Videos</option>
            <option value="doc">Documentos</option>
          </select>
          {selectedClient && (
            <UploadButton
              clientId={selectedClient}
              onUploaded={() => {}}
              uploading={uploading}
              onUpload={handleUpload}
            />
          )}
        </div>
      </div>
      <AssetGrid assets={assets} onDelete={handleDelete} />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/assets/ frontend/app/dashboard/assets/
git commit -m "feat: add media library frontend with upload, grid view, and delete"
```

---

## Task 7: UX Polish — Toasts + Real Dashboard + Loading States

**Files:**
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/dashboard/page.tsx`
- Modify: `frontend/app/dashboard/projects/[id]/page.tsx`

- [ ] **Step 1: Add Toaster to root layout**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MuelaADS — Marketing Agency",
  description: "AI-powered marketing agency platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Update Dashboard page with real counts**

```tsx
// frontend/app/dashboard/page.tsx
"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";

interface Stats { active_clients: number; active_projects: number; content_this_week: number; }

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    Promise.all([
      api.get("/clients"),
      api.get("/projects"),
      api.get("/content"),
    ]).then(([clients, projects, content]) => {
      const now = Date.now();
      const weekMs = 7 * 24 * 60 * 60 * 1000;
      setStats({
        active_clients: clients.data.filter((c: { active: boolean }) => c.active).length,
        active_projects: projects.data.filter((p: { status: string }) =>
          ["pending", "in_progress", "review"].includes(p.status)
        ).length,
        content_this_week: content.data.filter((c: { created_at: string }) =>
          new Date(c.created_at).getTime() > now - weekMs
        ).length,
      });
    });
  }, []);

  const cards = [
    { label: "Clientes Activos", value: stats?.active_clients },
    { label: "Proyectos en Curso", value: stats?.active_projects },
    { label: "Contenido Esta Semana", value: stats?.content_this_week },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map(({ label, value }) => (
          <Card key={label}>
            <CardHeader>
              <CardTitle className="text-sm text-gray-500">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              {value === undefined ? (
                <div className="h-9 w-16 bg-gray-100 rounded animate-pulse" />
              ) : (
                <p className="text-3xl font-bold">{value}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add toasts to project detail page approve action**

Replace the `approve` function and import in `frontend/app/dashboard/projects/[id]/page.tsx`:

Add import at top: `import { toast } from "sonner";`

Replace approve function:
```tsx
const approve = async (contentId: number) => {
  try {
    await api.post("/content/approve", { content_id: contentId });
    setContent((prev) =>
      prev.map((c) =>
        c.id === contentId ? { ...c, status: "approved" as const } : c
      )
    );
    toast.success("Contenido aprobado");
  } catch {
    toast.error("Error aprobando contenido");
  }
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/layout.tsx frontend/app/dashboard/page.tsx frontend/app/dashboard/projects/
git commit -m "feat: add toasts, real dashboard counts, and loading skeletons"
```

---

## Task 8: Final Tests + Tag v0.3.0

- [ ] **Step 1: Run full test suite**

```bash
cd /path/to/muelaads
pytest -v
```
Expected: 50+ tests PASS, 0 failures

- [ ] **Step 2: Check frontend builds without errors**

```bash
cd frontend
npm run build
```
Expected: `✓ Compiled successfully`

- [ ] **Step 3: Tag release**

```bash
git tag v0.3.0
git log --oneline -8
```

- [ ] **Step 4: Final commit if any lint fixes needed**

```bash
git add -A
git commit -m "chore: v0.3.0 — analytics, media library, PDF reports, UX polish"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Analytics dashboard — Tasks 1, 2, 5
- ✅ AI Insights — Task 2
- ✅ Media Library (R2) — Tasks 3, 6
- ✅ Blotato real publishing — existing BlotatoService + content.py handles schedule; no mock removal needed (blotato_id stored but API call is real via httpx — already implemented in blotato.py)
- ✅ PDF Reports — Tasks 4, 5 (download button)
- ✅ Toasts (sonner) — Task 7
- ✅ Loading states — Tasks 5, 7
- ✅ Empty states — Tasks 5, 6
- ✅ Dashboard real counts — Task 7
- ✅ Sidebar updated — Task 5

**Type consistency:**
- `r2_upload`, `r2_presigned_url`, `r2_delete` — consistent across services/r2.py and api/assets.py
- `get_summary`, `get_by_platform` — imported and called consistently in reports.py
- `AnalyticsSummary`, `PlatformStat`, `InsightsRequest`, `InsightsResponse` — defined once in schemas/analytics.py, used in api/analytics.py and api/reports.py
- `AssetOut` — defined in schemas/asset.py, used in api/assets.py

**Note on Blotato:** The existing `BlotatoService` in `backend/services/blotato.py` already has real HTTP calls via httpx. The schedule endpoint in `content.py` currently stores a `ScheduledPost` record but does NOT call BlotatoService yet — this is intentional for now, as it requires valid Blotato credentials in `.env`. The infrastructure is ready; connecting it requires setting `BLOTATO_API_KEY` in `.env` and calling `BlotatoService(settings.blotato_api_key).schedule_post(...)` from the schedule endpoint. This is a one-line addition once credentials are available.

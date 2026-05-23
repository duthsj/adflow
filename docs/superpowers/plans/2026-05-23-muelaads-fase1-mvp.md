# MuelaADS Fase 1 — MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MuelaADS internal system MVP: Auth, CRM, Projects, Social Media AI Agent, and Content Calendar with Blotato publishing.

**Architecture:** Next.js 14 App Router frontend + FastAPI backend + PostgreSQL. Six AI agents powered by Claude Sonnet 4.6. Social content auto-published via Blotato API. JWT auth with role-based access (admin/editor/designer).

**Tech Stack:** Next.js 14, Tailwind CSS, shadcn/ui, FastAPI, SQLAlchemy, PostgreSQL, Anthropic SDK, Blotato API, Cloudflare R2

---

## File Map

### Backend
```
backend/
├── main.py                     # FastAPI app, CORS, router registration
├── config.py                   # Pydantic Settings from env
├── database.py                 # SQLAlchemy engine, SessionLocal, Base
├── models/
│   ├── user.py                 # User ORM model
│   ├── client.py               # Client ORM model
│   ├── project.py              # Project ORM model
│   ├── content.py              # ContentItem ORM model
│   └── scheduled_post.py       # ScheduledPost ORM model
├── schemas/
│   ├── user.py                 # Pydantic user schemas
│   ├── client.py               # Pydantic client schemas
│   ├── project.py              # Pydantic project schemas
│   └── content.py              # Pydantic content schemas
├── api/
│   ├── deps.py                 # get_current_user dependency
│   ├── auth.py                 # /auth/login, /auth/register
│   ├── clients.py              # CRUD /clients
│   ├── projects.py             # CRUD /projects
│   └── content.py              # POST /content/generate, GET /content
├── agents/
│   ├── social_agent.py         # Claude-powered social media content generator
│   └── orchestrator.py        # Routes project to correct agent
├── services/
│   ├── blotato.py              # Blotato API client (schedule/publish)
│   └── r2.py                   # Cloudflare R2 upload/download
└── requirements.txt
```

### Frontend
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                # Redirect → /dashboard
│   ├── (auth)/login/page.tsx   # Login form
│   └── dashboard/
│       ├── layout.tsx          # Sidebar + header shell
│       ├── page.tsx            # Overview stats
│       ├── clients/
│       │   ├── page.tsx        # Client list
│       │   ├── new/page.tsx    # Create client
│       │   └── [id]/page.tsx   # Client detail
│       ├── projects/
│       │   ├── page.tsx        # Project list + kanban
│       │   ├── new/page.tsx    # Create project
│       │   └── [id]/page.tsx   # Project detail + agent interface
│       └── calendar/page.tsx   # Content calendar
├── components/
│   ├── layout/Sidebar.tsx
│   ├── layout/Header.tsx
│   ├── clients/ClientForm.tsx
│   ├── projects/ProjectForm.tsx
│   ├── projects/KanbanBoard.tsx
│   └── agents/ContentGenerator.tsx
├── lib/
│   ├── api.ts                  # Axios instance with JWT interceptor
│   └── auth.ts                 # Token storage helpers
└── types/index.ts              # Shared TypeScript types
```

---

## Task 1: Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/.env.example`
- Create: `frontend/package.json` (via create-next-app)

- [ ] **Step 1: Create backend directory and requirements**

```bash
mkdir -p backend/models backend/schemas backend/api backend/agents backend/services
```

Create `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pydantic-settings==2.4.0
anthropic==0.36.0
httpx==0.27.0
boto3==1.35.0
python-dotenv==1.0.0
alembic==1.13.3
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.0
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://muelaads:muelaads@localhost/muelaads"
    secret_key: str = "changeme-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    anthropic_api_key: str = ""
    blotato_api_key: str = ""
    r2_bucket: str = ""
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .api import auth, clients, projects, content

Base.metadata.create_all(bind=engine)

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
```

- [ ] **Step 5: Create .env.example**

```env
DATABASE_URL=postgresql://muelaads:muelaads@localhost/muelaads
SECRET_KEY=changeme-in-production
ANTHROPIC_API_KEY=sk-ant-...
BLOTATO_API_KEY=...
R2_BUCKET=muelaads-assets
R2_ENDPOINT=https://<accountid>.r2.cloudflarestorage.com
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
```

- [ ] **Step 6: Scaffold Next.js frontend**

```bash
cd /c/Users/Administrator/projects/muelaads
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
cd frontend
npx shadcn@latest init -d
npx shadcn@latest add button input label card badge table dialog form select textarea toast
npm install axios @tanstack/react-query zustand date-fns
```

- [ ] **Step 7: Create frontend/types/index.ts**

```typescript
export type Role = "admin" | "editor" | "designer";
export type ProjectStatus = "pending" | "in_progress" | "review" | "approved" | "delivered";
export type ServiceType = "social_media" | "ads" | "design" | "video" | "seo";
export type ContentStatus = "draft" | "review" | "approved" | "scheduled" | "published";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
}

export interface Client {
  id: number;
  name: string;
  industry: string;
  brand_guidelines: BrandGuidelines;
  social_accounts: SocialAccounts;
  active: boolean;
}

export interface BrandGuidelines {
  tone: string;
  colors: string[];
  fonts: string[];
  keywords: string[];
  avoid: string[];
}

export interface SocialAccounts {
  instagram?: string;
  facebook?: string;
  tiktok?: string;
  linkedin?: string;
  twitter?: string;
}

export interface Project {
  id: number;
  client_id: number;
  client?: Client;
  title: string;
  service_type: ServiceType;
  status: ProjectStatus;
  deadline: string;
  assigned_to?: number;
}

export interface ContentItem {
  id: number;
  project_id: number;
  type: string;
  body: string;
  status: ContentStatus;
  ai_generated: boolean;
  approved_by?: number;
  created_at: string;
}

export interface ScheduledPost {
  id: number;
  content_id: number;
  content?: ContentItem;
  platform: string;
  scheduled_at: string;
  published_at?: string;
  status: string;
}
```

- [ ] **Step 8: Create frontend/lib/api.ts**

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("muelaads_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("muelaads_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 9: Create frontend/lib/auth.ts**

```typescript
export const setToken = (token: string) => localStorage.setItem("muelaads_token", token);
export const getToken = () => localStorage.getItem("muelaads_token");
export const removeToken = () => localStorage.removeItem("muelaads_token");
export const isAuthenticated = () => !!getToken();
```

- [ ] **Step 10: Commit setup**

```bash
cd /c/Users/Administrator/projects/muelaads
git add .
git commit -m "feat: project setup — backend scaffold + Next.js frontend init"
```

---

## Task 2: Database Models

**Files:**
- Create: `backend/models/user.py`
- Create: `backend/models/client.py`
- Create: `backend/models/project.py`
- Create: `backend/models/content.py`
- Create: `backend/models/scheduled_post.py`
- Create: `backend/models/__init__.py`

- [ ] **Step 1: Create user model**

Create `backend/models/user.py`:
```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from ..database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    designer = "designer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.editor)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Create client model**

Create `backend/models/client.py`:
```python
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    brand_guidelines = Column(JSON, default={})
    social_accounts = Column(JSON, default={})
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: Create project model**

Create `backend/models/project.py`:
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class ProjectStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    review = "review"
    approved = "approved"
    delivered = "delivered"

class ServiceType(str, enum.Enum):
    social_media = "social_media"
    ads = "ads"
    design = "design"
    video = "video"
    seo = "seo"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.pending)
    deadline = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    client = relationship("Client", backref="projects")
```

- [ ] **Step 4: Create content model**

Create `backend/models/content.py`:
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class ContentStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    scheduled = "scheduled"
    published = "published"

class ContentItem(Base):
    __tablename__ = "content_items"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String, nullable=False)  # post, story, reel, ad_copy, blog
    body = Column(Text, nullable=False)
    status = Column(Enum(ContentStatus), default=ContentStatus.draft)
    ai_generated = Column(Boolean, default=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    project = relationship("Project", backref="content_items")
```

- [ ] **Step 5: Create scheduled_post model**

Create `backend/models/scheduled_post.py`:
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    platform = Column(String, nullable=False)  # instagram, facebook, tiktok, linkedin, twitter
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    blotato_id = Column(String, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, published, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = relationship("ContentItem", backref="scheduled_posts")
```

- [ ] **Step 6: Create models/__init__.py**

```python
from .user import User, UserRole
from .client import Client
from .project import Project, ProjectStatus, ServiceType
from .content import ContentItem, ContentStatus
from .scheduled_post import ScheduledPost
```

- [ ] **Step 7: Create PostgreSQL database**

```bash
# Run in psql or pgAdmin
createdb muelaads
createuser muelaads --pwprompt  # password: muelaads
psql -c "GRANT ALL PRIVILEGES ON DATABASE muelaads TO muelaads;"
```

Then start backend and let SQLAlchemy create tables:
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with actual values
python -c "from main import app; print('Tables created')"
```

- [ ] **Step 8: Commit models**

```bash
git add backend/models/
git commit -m "feat: database models — User, Client, Project, ContentItem, ScheduledPost"
```

---

## Task 3: Auth API (Backend)

**Files:**
- Create: `backend/schemas/user.py`
- Create: `backend/api/deps.py`
- Create: `backend/api/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Create user schemas**

Create `backend/schemas/user.py`:
```python
from pydantic import BaseModel, EmailStr
from ..models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.editor

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

- [ ] **Step 2: Write failing auth tests**

Create `tests/test_auth.py`:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={
        "email": "test@muelaads.com",
        "password": "password123",
        "name": "Test User",
        "role": "editor"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@muelaads.com"
    assert "access_token" in data

def test_login_success():
    client.post("/auth/register", json={
        "email": "login@muelaads.com",
        "password": "password123",
        "name": "Login User",
        "role": "editor"
    })
    response = client.post("/auth/login", json={
        "email": "login@muelaads.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    client.post("/auth/register", json={
        "email": "wrong@muelaads.com",
        "password": "correct",
        "name": "Wrong User",
        "role": "editor"
    })
    response = client.post("/auth/login", json={
        "email": "wrong@muelaads.com",
        "password": "incorrect"
    })
    assert response.status_code == 401
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /c/Users/Administrator/projects/muelaads
pytest tests/test_auth.py -v
```

Expected: `ImportError` or `404` — auth routes don't exist yet.

- [ ] **Step 4: Create deps.py**

Create `backend/api/deps.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..config import settings

bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 5: Create auth.py router**

Create `backend/api/auth.py`:
```python
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, Token, LoginRequest
from ..config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.secret_key, algorithm=settings.algorithm)

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
def me(current_user: User = Depends(get_current_user_from_auth)):
    return current_user
```

Fix the me endpoint — import properly:
```python
from ..api.deps import get_current_user

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_auth.py -v
```

Expected: 3 PASSED

- [ ] **Step 7: Commit auth**

```bash
git add backend/schemas/user.py backend/api/deps.py backend/api/auth.py tests/test_auth.py
git commit -m "feat: auth API — register, login, JWT, get_current_user"
```

---

## Task 4: Clients API (Backend)

**Files:**
- Create: `backend/schemas/client.py`
- Create: `backend/api/clients.py`
- Create: `tests/test_clients.py`

- [ ] **Step 1: Create client schemas**

Create `backend/schemas/client.py`:
```python
from pydantic import BaseModel
from typing import Optional

class BrandGuidelines(BaseModel):
    tone: str = ""
    colors: list[str] = []
    fonts: list[str] = []
    keywords: list[str] = []
    avoid: list[str] = []

class SocialAccounts(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None

class ClientCreate(BaseModel):
    name: str
    industry: str
    brand_guidelines: BrandGuidelines = BrandGuidelines()
    social_accounts: SocialAccounts = SocialAccounts()

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    brand_guidelines: Optional[BrandGuidelines] = None
    social_accounts: Optional[SocialAccounts] = None
    active: Optional[bool] = None

class ClientOut(BaseModel):
    id: int
    name: str
    industry: str
    brand_guidelines: dict
    social_accounts: dict
    active: bool

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_clients.py`:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def get_token():
    client.post("/auth/register", json={
        "email": "admin@muelaads.com", "password": "pass123",
        "name": "Admin", "role": "admin"
    })
    r = client.post("/auth/login", json={"email": "admin@muelaads.com", "password": "pass123"})
    return r.json()["access_token"]

def test_create_client():
    token = get_token()
    response = client.post("/clients", json={
        "name": "Acme Corp",
        "industry": "Technology",
        "brand_guidelines": {"tone": "professional", "colors": ["#000", "#fff"], "fonts": [], "keywords": [], "avoid": []},
        "social_accounts": {"instagram": "@acme"}
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corp"

def test_list_clients():
    token = get_token()
    client.post("/clients", json={"name": "Test Co", "industry": "Retail"}, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/clients", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_get_client():
    token = get_token()
    created = client.post("/clients", json={"name": "Get Co", "industry": "Food"}, headers={"Authorization": f"Bearer {token}"}).json()
    r = client.get(f"/clients/{created['id']}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["name"] == "Get Co"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_clients.py -v
```

Expected: FAIL — `/clients` routes don't exist.

- [ ] **Step 4: Create clients.py router**

Create `backend/api/clients.py`:
```python
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
        setattr(client, field, value if not hasattr(value, "model_dump") else value.model_dump())
    db.commit()
    db.refresh(client)
    return client
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_clients.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit clients API**

```bash
git add backend/schemas/client.py backend/api/clients.py tests/test_clients.py
git commit -m "feat: clients CRUD API"
```

---

## Task 5: Projects API (Backend)

**Files:**
- Create: `backend/schemas/project.py`
- Create: `backend/api/projects.py`
- Create: `tests/test_projects.py`

- [ ] **Step 1: Create project schemas**

Create `backend/schemas/project.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.project import ProjectStatus, ServiceType

class ProjectCreate(BaseModel):
    client_id: int
    title: str
    service_type: ServiceType
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ProjectStatus] = None
    deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None

class ProjectOut(BaseModel):
    id: int
    client_id: int
    title: str
    service_type: ServiceType
    status: ProjectStatus
    deadline: Optional[datetime]
    assigned_to: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_projects.py`:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def get_token_and_client_id():
    client.post("/auth/register", json={"email": "p@m.com", "password": "pass", "name": "P", "role": "admin"})
    token = client.post("/auth/login", json={"email": "p@m.com", "password": "pass"}).json()["access_token"]
    c = client.post("/clients", json={"name": "C", "industry": "I"}, headers={"Authorization": f"Bearer {token}"}).json()
    return token, c["id"]

def test_create_project():
    token, client_id = get_token_and_client_id()
    r = client.post("/projects", json={
        "client_id": client_id,
        "title": "January Social Media",
        "service_type": "social_media"
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["title"] == "January Social Media"
    assert r.json()["status"] == "pending"

def test_update_project_status():
    token, client_id = get_token_and_client_id()
    p = client.post("/projects", json={"client_id": client_id, "title": "P", "service_type": "ads"},
                    headers={"Authorization": f"Bearer {token}"}).json()
    r = client.put(f"/projects/{p['id']}", json={"status": "in_progress"},
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_projects.py -v
```

Expected: FAIL — routes don't exist.

- [ ] **Step 4: Create projects.py router**

Create `backend/api/projects.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.project import Project
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from ..api.deps import get_current_user

router = APIRouter()

@router.post("", response_model=ProjectOut)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("", response_model=list[ProjectOut])
def list_projects(client_id: int = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Project)
    if client_id:
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
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_projects.py -v
```

Expected: 2 PASSED

- [ ] **Step 6: Commit projects API**

```bash
git add backend/schemas/project.py backend/api/projects.py tests/test_projects.py
git commit -m "feat: projects CRUD API"
```

---

## Task 6: Social Media Agent (AI)

**Files:**
- Create: `backend/agents/social_agent.py`
- Create: `backend/agents/orchestrator.py`
- Create: `backend/schemas/content.py`
- Create: `backend/api/content.py`
- Create: `tests/test_agents.py`

- [ ] **Step 1: Create content schemas**

Create `backend/schemas/content.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.content import ContentStatus

class GenerateContentRequest(BaseModel):
    project_id: int
    content_type: str  # post, story, reel, carousel
    instructions: Optional[str] = None  # extra instructions from editor

class ContentItemOut(BaseModel):
    id: int
    project_id: int
    type: str
    body: str
    status: ContentStatus
    ai_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ApproveContentRequest(BaseModel):
    content_id: int

class ScheduleContentRequest(BaseModel):
    content_id: int
    platform: str
    scheduled_at: datetime
```

- [ ] **Step 2: Create social_agent.py**

Create `backend/agents/social_agent.py`:
```python
import anthropic
from ..config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are an expert social media copywriter for a marketing agency.
You write engaging, platform-appropriate content that matches the client's brand voice.
Always return ONLY the content text — no explanations, no headers, no meta-commentary.
Write in the language that matches the brand tone (Spanish if tone mentions it, otherwise English)."""

def generate_social_post(
    brand_guidelines: dict,
    content_type: str,
    client_name: str,
    instructions: str = ""
) -> str:
    tone = brand_guidelines.get("tone", "professional")
    keywords = brand_guidelines.get("keywords", [])
    avoid = brand_guidelines.get("avoid", [])
    colors = brand_guidelines.get("colors", [])

    user_prompt = f"""Client: {client_name}
Content type: {content_type}
Brand tone: {tone}
Keywords to include: {", ".join(keywords) if keywords else "none specified"}
Things to avoid: {", ".join(avoid) if avoid else "none specified"}
{"Additional instructions: " + instructions if instructions else ""}

Write a {content_type} for this client's social media. Include relevant hashtags at the end."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text
```

- [ ] **Step 3: Create orchestrator.py**

Create `backend/agents/orchestrator.py`:
```python
from ..models.project import ServiceType
from .social_agent import generate_social_post

def generate_content(
    service_type: str,
    content_type: str,
    client_name: str,
    brand_guidelines: dict,
    instructions: str = ""
) -> str:
    if service_type == ServiceType.social_media:
        return generate_social_post(
            brand_guidelines=brand_guidelines,
            content_type=content_type,
            client_name=client_name,
            instructions=instructions,
        )
    # Future: ads_agent, seo_agent, etc.
    raise ValueError(f"Agent for service_type '{service_type}' not yet implemented")
```

- [ ] **Step 4: Write failing test for agent**

Create `tests/test_agents.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from backend.agents.social_agent import generate_social_post

def test_generate_social_post_calls_claude():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Exciting new product! #innovation #tech")]

    with patch("backend.agents.social_agent.client.messages.create", return_value=mock_message):
        result = generate_social_post(
            brand_guidelines={"tone": "energetic", "keywords": ["innovation"], "avoid": [], "colors": []},
            content_type="post",
            client_name="Acme Corp",
            instructions="Focus on our new product launch"
        )

    assert "innovation" in result.lower() or len(result) > 0

def test_generate_social_post_returns_string():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Test post content #hashtag")]

    with patch("backend.agents.social_agent.client.messages.create", return_value=mock_message):
        result = generate_social_post(
            brand_guidelines={},
            content_type="story",
            client_name="Test Client"
        )

    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 5: Run tests to verify they fail**

```bash
pytest tests/test_agents.py -v
```

Expected: FAIL — `ImportError` or module not found.

- [ ] **Step 6: Create content API router**

Create `backend/api/content.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.content import ContentItem, ContentStatus
from ..models.project import Project
from ..models.user import User
from ..models.scheduled_post import ScheduledPost
from ..schemas.content import GenerateContentRequest, ContentItemOut, ApproveContentRequest, ScheduleContentRequest
from ..agents.orchestrator import generate_content
from ..api.deps import get_current_user

router = APIRouter()

@router.post("/generate", response_model=ContentItemOut)
def generate(data: GenerateContentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    body = generate_content(
        service_type=project.service_type.value,
        content_type=data.content_type,
        client_name=project.client.name,
        brand_guidelines=project.client.brand_guidelines or {},
        instructions=data.instructions or "",
    )

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
    if project_id:
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
    return post
```

- [ ] **Step 7: Run agent tests to verify they pass**

```bash
pytest tests/test_agents.py -v
```

Expected: 2 PASSED

- [ ] **Step 8: Commit agents + content API**

```bash
git add backend/agents/ backend/schemas/content.py backend/api/content.py tests/test_agents.py
git commit -m "feat: social media AI agent + content generation API"
```

---

## Task 7: Blotato Integration

**Files:**
- Create: `backend/services/blotato.py`
- Create: `tests/test_blotato.py`

- [ ] **Step 1: Write failing blotato test**

Create `tests/test_blotato.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from backend.services.blotato import BlotatoService

def test_blotato_schedule_post():
    service = BlotatoService(api_key="test-key")
    with patch.object(service, "_post", return_value={"id": "blotato-123", "status": "scheduled"}):
        result = service.schedule_post(
            platform="instagram",
            content="Test post #test",
            scheduled_at="2026-06-01T10:00:00Z",
            media_urls=[]
        )
    assert result["id"] == "blotato-123"
    assert result["status"] == "scheduled"
```

- [ ] **Step 2: Run to verify fail**

```bash
pytest tests/test_blotato.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Create blotato.py service**

Create `backend/services/blotato.py`:
```python
import httpx
from typing import Optional

BLOTATO_BASE_URL = "https://api.blotato.com/v1"

class BlotatoService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict) -> dict:
        with httpx.Client() as client:
            r = client.post(f"{BLOTATO_BASE_URL}/{endpoint}", json=payload, headers=self.headers, timeout=30)
            r.raise_for_status()
            return r.json()

    def schedule_post(
        self,
        platform: str,
        content: str,
        scheduled_at: str,
        media_urls: Optional[list[str]] = None,
    ) -> dict:
        payload = {
            "platform": platform,
            "content": content,
            "scheduled_at": scheduled_at,
            "media": [{"url": u} for u in (media_urls or [])],
        }
        return self._post("posts/schedule", payload)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/test_blotato.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Commit Blotato service**

```bash
git add backend/services/blotato.py tests/test_blotato.py
git commit -m "feat: Blotato API service for social scheduling"
```

---

## Task 8: Auth Frontend

**Files:**
- Create: `frontend/app/(auth)/login/page.tsx`
- Create: `frontend/app/(auth)/layout.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create root redirect**

Replace `frontend/app/page.tsx`:
```tsx
import { redirect } from "next/navigation";
export default function Home() {
  redirect("/dashboard");
}
```

- [ ] **Step 2: Create auth layout**

Create `frontend/app/(auth)/layout.tsx`:
```tsx
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
```

- [ ] **Step 3: Create login page**

Create `frontend/app/(auth)/login/page.tsx`:
```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setToken(data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">MuelaADS</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label htmlFor="password">Contraseña</Label>
            <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Ingresando..." : "Ingresar"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Commit auth frontend**

```bash
git add frontend/app/
git commit -m "feat: login page frontend"
```

---

## Task 9: Dashboard Layout + Sidebar

**Files:**
- Create: `frontend/components/layout/Sidebar.tsx`
- Create: `frontend/components/layout/Header.tsx`
- Create: `frontend/app/dashboard/layout.tsx`
- Create: `frontend/app/dashboard/page.tsx`

- [ ] **Step 1: Create Sidebar**

Create `frontend/components/layout/Sidebar.tsx`:
```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, FolderKanban, Calendar, LogOut } from "lucide-react";
import { removeToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/clients", label: "Clientes", icon: Users },
  { href: "/dashboard/projects", label: "Proyectos", icon: FolderKanban },
  { href: "/dashboard/calendar", label: "Calendario", icon: Calendar },
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
          <Link key={href} href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              pathname === href ? "bg-orange-500 text-white" : "text-gray-300 hover:bg-gray-800"
            )}>
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <button onClick={logout} className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white w-full">
          <LogOut size={18} />
          Salir
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Create dashboard layout**

Create `frontend/app/dashboard/layout.tsx`:
```tsx
import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">{children}</main>
    </div>
  );
}
```

- [ ] **Step 3: Create dashboard overview page**

Create `frontend/app/dashboard/page.tsx`:
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-sm text-gray-500">Clientes Activos</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">—</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm text-gray-500">Proyectos en Curso</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">—</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm text-gray-500">Contenido Esta Semana</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">—</p></CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit dashboard layout**

```bash
git add frontend/components/ frontend/app/dashboard/
git commit -m "feat: dashboard layout with sidebar navigation"
```

---

## Task 10: Clients Frontend

**Files:**
- Create: `frontend/app/dashboard/clients/page.tsx`
- Create: `frontend/app/dashboard/clients/new/page.tsx`
- Create: `frontend/components/clients/ClientForm.tsx`

- [ ] **Step 1: Create ClientForm component**

Create `frontend/components/clients/ClientForm.tsx`:
```tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ClientForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "", industry: "",
    brand_guidelines: { tone: "", colors: "", keywords: "", avoid: "" },
    social_accounts: { instagram: "", facebook: "", tiktok: "" }
  });

  const set = (key: string, value: string) => setForm(f => ({ ...f, [key]: value }));
  const setBrand = (key: string, value: string) => setForm(f => ({ ...f, brand_guidelines: { ...f.brand_guidelines, [key]: value } }));
  const setSocial = (key: string, value: string) => setForm(f => ({ ...f, social_accounts: { ...f.social_accounts, [key]: value } }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/clients", {
        name: form.name,
        industry: form.industry,
        brand_guidelines: {
          tone: form.brand_guidelines.tone,
          colors: form.brand_guidelines.colors.split(",").map(s => s.trim()).filter(Boolean),
          keywords: form.brand_guidelines.keywords.split(",").map(s => s.trim()).filter(Boolean),
          avoid: form.brand_guidelines.avoid.split(",").map(s => s.trim()).filter(Boolean),
          fonts: [],
        },
        social_accounts: form.social_accounts,
      });
      router.push("/dashboard/clients");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Nombre del cliente</Label>
          <Input value={form.name} onChange={e => set("name", e.target.value)} required />
        </div>
        <div>
          <Label>Industria</Label>
          <Input value={form.industry} onChange={e => set("industry", e.target.value)} required />
        </div>
      </div>
      <div>
        <h3 className="font-semibold mb-3">Brand Guidelines</h3>
        <div className="space-y-3">
          <div>
            <Label>Tono de voz</Label>
            <Input placeholder="ej: profesional, cercano, divertido" value={form.brand_guidelines.tone} onChange={e => setBrand("tone", e.target.value)} />
          </div>
          <div>
            <Label>Keywords (separadas por coma)</Label>
            <Input placeholder="ej: innovación, calidad, confianza" value={form.brand_guidelines.keywords} onChange={e => setBrand("keywords", e.target.value)} />
          </div>
          <div>
            <Label>Evitar (separadas por coma)</Label>
            <Input placeholder="ej: competencia, precio, descuento" value={form.brand_guidelines.avoid} onChange={e => setBrand("avoid", e.target.value)} />
          </div>
        </div>
      </div>
      <div>
        <h3 className="font-semibold mb-3">Redes Sociales</h3>
        <div className="grid grid-cols-3 gap-3">
          <div><Label>Instagram</Label><Input placeholder="@handle" value={form.social_accounts.instagram} onChange={e => setSocial("instagram", e.target.value)} /></div>
          <div><Label>Facebook</Label><Input placeholder="página" value={form.social_accounts.facebook} onChange={e => setSocial("facebook", e.target.value)} /></div>
          <div><Label>TikTok</Label><Input placeholder="@handle" value={form.social_accounts.tiktok} onChange={e => setSocial("tiktok", e.target.value)} /></div>
        </div>
      </div>
      <Button type="submit" disabled={loading}>{loading ? "Guardando..." : "Crear Cliente"}</Button>
    </form>
  );
}
```

- [ ] **Step 2: Create clients list page**

Create `frontend/app/dashboard/clients/page.tsx`:
```tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Client } from "@/types";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);

  useEffect(() => {
    api.get("/clients").then(r => setClients(r.data));
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <Link href="/dashboard/clients/new">
          <Button>+ Nuevo Cliente</Button>
        </Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clients.map(c => (
          <Link key={c.id} href={`/dashboard/clients/${c.id}`}>
            <div className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex justify-between items-start">
                <h3 className="font-semibold text-gray-900">{c.name}</h3>
                <Badge variant={c.active ? "default" : "secondary"}>{c.active ? "Activo" : "Inactivo"}</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">{c.industry}</p>
              {c.brand_guidelines.tone && (
                <p className="text-xs text-gray-400 mt-2">Tono: {c.brand_guidelines.tone}</p>
              )}
            </div>
          </Link>
        ))}
        {clients.length === 0 && (
          <p className="text-gray-400 col-span-3 text-center py-12">No hay clientes aún. Crea el primero.</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create new client page**

Create `frontend/app/dashboard/clients/new/page.tsx`:
```tsx
import ClientForm from "@/components/clients/ClientForm";

export default function NewClientPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Nuevo Cliente</h1>
      <ClientForm />
    </div>
  );
}
```

- [ ] **Step 4: Commit clients frontend**

```bash
git add frontend/app/dashboard/clients/ frontend/components/clients/
git commit -m "feat: clients frontend — list and create"
```

---

## Task 11: Projects Frontend + Content Generator

**Files:**
- Create: `frontend/app/dashboard/projects/page.tsx`
- Create: `frontend/app/dashboard/projects/new/page.tsx`
- Create: `frontend/app/dashboard/projects/[id]/page.tsx`
- Create: `frontend/components/agents/ContentGenerator.tsx`

- [ ] **Step 1: Create projects list page**

Create `frontend/app/dashboard/projects/page.tsx`:
```tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Project } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  pending: "secondary",
  in_progress: "default",
  review: "outline",
  approved: "default",
  delivered: "secondary",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  review: "Revisión",
  approved: "Aprobado",
  delivered: "Entregado",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.get("/projects").then(r => setProjects(r.data));
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Proyectos</h1>
        <Link href="/dashboard/projects/new"><Button>+ Nuevo Proyecto</Button></Link>
      </div>
      <div className="bg-white border rounded-lg divide-y">
        {projects.map(p => (
          <Link key={p.id} href={`/dashboard/projects/${p.id}`}>
            <div className="flex items-center justify-between p-4 hover:bg-gray-50">
              <div>
                <h3 className="font-medium">{p.title}</h3>
                <p className="text-sm text-gray-500">{p.service_type.replace("_", " ")}</p>
              </div>
              <Badge variant={STATUS_COLORS[p.status] as any}>{STATUS_LABELS[p.status]}</Badge>
            </div>
          </Link>
        ))}
        {projects.length === 0 && (
          <p className="text-center text-gray-400 py-12">No hay proyectos. Crea el primero.</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create new project page**

Create `frontend/app/dashboard/projects/new/page.tsx`:
```tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import api from "@/lib/api";
import { Client } from "@/types";

export default function NewProjectPage() {
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState({ client_id: "", title: "", service_type: "" });

  useEffect(() => {
    api.get("/clients").then(r => setClients(r.data));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post("/projects", { ...form, client_id: parseInt(form.client_id) });
    router.push("/dashboard/projects");
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Nuevo Proyecto</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <div>
          <Label>Cliente</Label>
          <Select onValueChange={v => setForm(f => ({ ...f, client_id: v }))}>
            <SelectTrigger><SelectValue placeholder="Seleccionar cliente" /></SelectTrigger>
            <SelectContent>
              {clients.map(c => <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Título</Label>
          <Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
        </div>
        <div>
          <Label>Tipo de servicio</Label>
          <Select onValueChange={v => setForm(f => ({ ...f, service_type: v }))}>
            <SelectTrigger><SelectValue placeholder="Seleccionar servicio" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="social_media">Redes Sociales</SelectItem>
              <SelectItem value="ads">Publicidad</SelectItem>
              <SelectItem value="design">Diseño</SelectItem>
              <SelectItem value="video">Video</SelectItem>
              <SelectItem value="seo">SEO</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button type="submit">Crear Proyecto</Button>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Create ContentGenerator component**

Create `frontend/components/agents/ContentGenerator.tsx`:
```tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { ContentItem } from "@/types";

interface Props {
  projectId: number;
  onGenerated: (item: ContentItem) => void;
}

export default function ContentGenerator({ projectId, onGenerated }: Props) {
  const [contentType, setContentType] = useState("post");
  const [instructions, setInstructions] = useState("");
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/content/generate", {
        project_id: projectId,
        content_type: contentType,
        instructions,
      });
      onGenerated(data);
      setInstructions("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border rounded-lg p-6 space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="font-semibold">Generar Contenido AI</h3>
        <Badge variant="secondary">Claude Sonnet 4.6</Badge>
      </div>
      <div>
        <Label>Tipo de contenido</Label>
        <Select value={contentType} onValueChange={setContentType}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="post">Post</SelectItem>
            <SelectItem value="story">Story</SelectItem>
            <SelectItem value="reel">Reel (caption)</SelectItem>
            <SelectItem value="carousel">Carrusel</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Instrucciones adicionales (opcional)</Label>
        <Textarea
          placeholder="ej: Enfocarse en el lanzamiento del nuevo producto, incluir CTA para link en bio..."
          value={instructions}
          onChange={e => setInstructions(e.target.value)}
          rows={3}
        />
      </div>
      <Button onClick={generate} disabled={loading} className="w-full">
        {loading ? "Generando..." : "Generar con AI"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Create project detail page**

Create `frontend/app/dashboard/projects/[id]/page.tsx`:
```tsx
"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ContentGenerator from "@/components/agents/ContentGenerator";
import api from "@/lib/api";
import { Project, ContentItem } from "@/types";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);

  useEffect(() => {
    api.get(`/projects/${id}`).then(r => setProject(r.data));
    api.get(`/content?project_id=${id}`).then(r => setContent(r.data));
  }, [id]);

  const handleGenerated = (item: ContentItem) => {
    setContent(prev => [item, ...prev]);
  };

  const approve = async (contentId: number) => {
    await api.post("/content/approve", { content_id: contentId });
    setContent(prev => prev.map(c => c.id === contentId ? { ...c, status: "approved" as any } : c));
  };

  if (!project) return <div className="text-gray-400">Cargando...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{project.title}</h1>
        <p className="text-gray-500">{project.service_type.replace("_", " ")} · {project.status}</p>
      </div>

      {project.service_type === "social_media" && (
        <ContentGenerator projectId={project.id} onGenerated={handleGenerated} />
      )}

      <div>
        <h2 className="font-semibold mb-3">Contenido generado ({content.length})</h2>
        <div className="space-y-3">
          {content.map(c => (
            <div key={c.id} className="bg-white border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <Badge variant="outline">{c.type}</Badge>
                <Badge variant={c.status === "approved" ? "default" : "secondary"}>{c.status}</Badge>
              </div>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{c.body}</p>
              {c.status === "draft" && (
                <Button size="sm" variant="outline" className="mt-3" onClick={() => approve(c.id)}>
                  Aprobar
                </Button>
              )}
            </div>
          ))}
          {content.length === 0 && (
            <p className="text-gray-400 text-center py-8">Sin contenido aún. Genera el primero.</p>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit projects frontend**

```bash
git add frontend/app/dashboard/projects/ frontend/components/agents/
git commit -m "feat: projects frontend + AI content generator interface"
```

---

## Task 12: PM2 Deploy Config

**Files:**
- Create: `ecosystem.config.js`
- Create: `start.sh`

- [ ] **Step 1: Create PM2 ecosystem**

Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: "muelaads-backend",
      cwd: "./backend",
      script: "uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000 --reload",
      interpreter: "python",
      env: { PYTHONPATH: "." },
    },
    {
      name: "muelaads-frontend",
      cwd: "./frontend",
      script: "npm",
      args: "run dev",
      env: { PORT: "3000", NEXT_PUBLIC_API_URL: "http://localhost:8000" },
    },
  ],
};
```

- [ ] **Step 2: Create start script**

Create `start.sh`:
```bash
#!/bin/bash
echo "Installing backend deps..."
cd backend && pip install -r requirements.txt && cd ..

echo "Installing frontend deps..."
cd frontend && npm install && cd ..

echo "Starting MuelaADS with PM2..."
pm2 start ecosystem.config.js
pm2 save
echo "MuelaADS running at http://localhost:3000"
```

```bash
chmod +x start.sh
```

- [ ] **Step 3: Test full startup**

```bash
cd /c/Users/Administrator/projects/muelaads
bash start.sh
```

Open http://localhost:3000 — should redirect to login.

- [ ] **Step 4: Final commit**

```bash
git add ecosystem.config.js start.sh
git commit -m "feat: PM2 deploy config + start script"
```

---

## Task 13: Run All Tests

- [ ] **Step 1: Run full test suite**

```bash
cd /c/Users/Administrator/projects/muelaads
pytest tests/ -v
```

Expected output:
```
tests/test_auth.py::test_register_user PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_clients.py::test_create_client PASSED
tests/test_clients.py::test_list_clients PASSED
tests/test_clients.py::test_get_client PASSED
tests/test_projects.py::test_create_project PASSED
tests/test_projects.py::test_update_project_status PASSED
tests/test_agents.py::test_generate_social_post_calls_claude PASSED
tests/test_agents.py::test_generate_social_post_returns_string PASSED
tests/test_blotato.py::test_blotato_schedule_post PASSED

11 passed
```

- [ ] **Step 2: Tag Fase 1 complete**

```bash
git tag v0.1.0 -m "MuelaADS Fase 1 MVP"
```

---

## Environment Variables Required

Create `backend/.env` (copy from `.env.example`):

| Variable | Obtener de |
|----------|-----------|
| `DATABASE_URL` | PostgreSQL local |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `BLOTATO_API_KEY` | blotato.com/dashboard |
| `R2_*` | Cloudflare dashboard |

---

*Fase 2 cubrirá: Ads Agent, SEO Agent, Design Agent, Video Agent, Portal de Aprobaciones cliente.*

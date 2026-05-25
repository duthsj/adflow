from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models  # noqa: F401 — must import before create_all
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

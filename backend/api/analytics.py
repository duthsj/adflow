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
import anthropic
from ..config import settings

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

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
                ContentItem.created_at >= since,
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
        p = platforms.setdefault(row.platform, {
            "posts": 0,
            "reach": 0.0,
            "engagement": 0.0,
            "reach_count": 0,
            "eng_count": 0,
        })
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

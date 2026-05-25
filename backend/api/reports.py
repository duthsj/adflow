from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.client import Client
from ..models.user import User
from ..api.analytics import get_summary, get_by_platform
from ..schemas.analytics import InsightsRequest
from ..services.report import generate_pdf
from ..api.deps import get_current_user
from ..config import settings

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

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

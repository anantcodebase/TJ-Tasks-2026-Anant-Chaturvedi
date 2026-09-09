from fastapi import APIRouter, Query
from app.models import AnalyticsMetric, AnalyticsResult
from app.tools.analytics import query_analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResult)
async def analytics(metric: AnalyticsMetric = Query(default="engagement")) -> AnalyticsResult:
    return await query_analytics(metric)

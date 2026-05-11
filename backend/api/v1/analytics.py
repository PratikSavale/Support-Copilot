from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from schemas.analytics import (
    AnalyticsDateRange,
    AnalyticsIssuesResponse,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)
from services.service_factory import get_analytics_service

router = APIRouter()

analytics_service = get_analytics_service()

def _get_days_from_range(date_range: AnalyticsDateRange | None) -> int:
    if date_range == AnalyticsDateRange.last_30d:
        return 30
    elif date_range == AnalyticsDateRange.last_90d:
        return 90
    return 7  # Default to 7 days

@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
)
async def analytics_overview(
    date_range: AnalyticsDateRange | None = Query(
        None,
        description="Preset window; Person 4 may add explicit start/end dates.",
    ),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    days = _get_days_from_range(date_range)
    metrics = await analytics_service.get_overview(db, days=days)
    trends = await analytics_service.get_trends(db, days=days)
    common_issues = await analytics_service.get_common_issues(db, limit=5)
    
    return AnalyticsOverviewResponse(
        metrics=metrics,
        trends=trends,
        common_issues=common_issues,
    )

@router.get(
    "/trends",
    response_model=AnalyticsTrendsResponse,
)
async def analytics_trends(
    date_range: AnalyticsDateRange | None = Query(None),
    granularity: str | None = Query(
        None,
        description="e.g. day|week — Person 4 defines allowed values",
    ),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsTrendsResponse:
    days = _get_days_from_range(date_range)
    # metric_type could be added as query param, defaulting to query_count for now
    trends = await analytics_service.get_trends(db, days=days, metric_type="query_count")
    return AnalyticsTrendsResponse(trends=trends)

@router.get(
    "/issues",
    response_model=AnalyticsIssuesResponse,
)
async def analytics_issues(
    limit: int = Query(20, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsIssuesResponse:
    issues = await analytics_service.get_common_issues(db, limit=limit)
    return AnalyticsIssuesResponse(issues=issues)

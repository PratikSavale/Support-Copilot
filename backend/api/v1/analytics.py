from fastapi import APIRouter, HTTPException, Query, status

from schemas.analytics import (
    AnalyticsDateRange,
    AnalyticsIssuesResponse,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)

router = APIRouter()


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def analytics_overview(
    date_range: AnalyticsDateRange | None = Query(
        None,
        description="Preset window; Person 4 may add explicit start/end dates.",
    ),
) -> AnalyticsOverviewResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/trends",
    response_model=AnalyticsTrendsResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def analytics_trends(
    date_range: AnalyticsDateRange | None = Query(None),
    granularity: str | None = Query(
        None,
        description="e.g. day|week — Person 4 defines allowed values",
    ),
) -> AnalyticsTrendsResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/issues",
    response_model=AnalyticsIssuesResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def analytics_issues(
    limit: int = Query(20, ge=1, le=500),
) -> AnalyticsIssuesResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )

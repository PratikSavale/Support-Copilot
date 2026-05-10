from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class AnalyticsDateRange(str, Enum):
    """Convenience presets — Person 4 may also accept raw start/end dates."""

    last_7d = "last_7d"
    last_30d = "last_30d"
    last_90d = "last_90d"


class MetricOverview(BaseModel):
    total_queries: int = 0
    resolution_rate: float = 0.0
    escalation_rate: float = 0.0
    avg_confidence_score: float = 0.0
    total_tickets: int = 0
    total_sessions: int = 0


class TrendPoint(BaseModel):
    date: date
    value: int
    label: str


class CommonIssue(BaseModel):
    pattern: str
    count: int
    severity: str
    last_seen: datetime


class AnalyticsOverviewResponse(BaseModel):
    """Dashboard payload — aligns with plans; wire name `metrics` kept nested per architecture."""

    metrics: MetricOverview
    trends: list[TrendPoint] = []
    common_issues: list[CommonIssue] = []


class AnalyticsTrendsResponse(BaseModel):
    trends: list[TrendPoint]


class AnalyticsIssuesResponse(BaseModel):
    issues: list[CommonIssue] = Field(default_factory=list)

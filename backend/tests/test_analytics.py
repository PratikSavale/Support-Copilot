import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from config.database import get_db
from schemas.analytics import MetricOverview

@pytest.fixture
def mock_analytics_service():
    # Use AsyncMock for the service methods since they are awaited in the API
    with patch("api.v1.analytics.analytics_service") as mock:
        mock.get_overview = AsyncMock(return_value=MetricOverview(
            total_queries=10,
            resolution_rate=80.0,
            escalation_rate=10.0,
            avg_confidence_score=0.85,
            total_tickets=1,
            total_sessions=5
        ))
        mock.get_trends = AsyncMock(return_value=[])
        mock.get_common_issues = AsyncMock(return_value=[])
        yield mock

@pytest.fixture
def mock_db():
    # Override get_db to avoid real DB connections
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client(mock_db, mock_analytics_service):
    return TestClient(app)

def test_analytics_overview_stub(client):
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data

def test_analytics_trends_stub(client):
    response = client.get("/api/v1/analytics/trends")
    assert response.status_code == 200

def test_analytics_issues_stub(client):
    response = client.get("/api/v1/analytics/issues")
    assert response.status_code == 200

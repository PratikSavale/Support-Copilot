"""
Jira Cloud API client with mock fallback for demo reliability.

When JIRA_API_TOKEN is empty the client transparently returns fake issue keys
so the rest of the pipeline never breaks during a demo.
"""

from __future__ import annotations

import base64
import uuid
from typing import Any

import httpx

from config.settings import get_settings


class JiraClient:
    """Async wrapper around Jira Cloud REST API v3."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = (settings.JIRA_URL or "https://jira.example.com").rstrip("/")
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY
        # Fall back to mock when credentials are missing.
        self.use_mock = not self.api_token

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_ticket(self, ticket: Any) -> dict[str, Any]:
        """Create a Jira issue from a Ticket ORM instance.

        Returns dict with at least ``key`` and ``id`` fields.
        """
        if self.use_mock:
            return self._mock_create_ticket(ticket)

        url = f"{self.base_url}/rest/api/3/issue"
        headers = self._headers()

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": (ticket.summary or "Support escalation")[:255],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": ticket.description or "",
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
                "priority": self._map_severity_to_priority(
                    getattr(ticket, "severity", None)
                ),
                "labels": ["copilot-escalation"],
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {"key": data.get("key"), "id": data.get("id")}

    async def get_ticket(self, issue_key: str) -> dict[str, Any] | None:
        """Fetch a Jira issue by its key (e.g. SUP-123)."""
        if self.use_mock:
            return {"key": issue_key, "status": "Open"}

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        credentials = f"{self.email}:{self.api_token}"
        b64 = base64.b64encode(credentials.encode()).decode()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {b64}",
        }

    @staticmethod
    def _map_severity_to_priority(severity: Any) -> dict[str, str]:
        """Map our severity enum/string to a Jira v3 priority object."""
        raw = severity.value if hasattr(severity, "value") else str(severity or "medium")
        mapping = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "critical": "Highest",
        }
        return {"name": mapping.get(raw, "Medium")}

    def _mock_create_ticket(self, ticket: Any) -> dict[str, Any]:
        """Return a fake Jira response for demo purposes."""
        mock_key = f"SUP-{uuid.uuid4().hex[:6].upper()}"
        return {
            "key": mock_key,
            "id": str(getattr(ticket, "id", uuid.uuid4())),
            "self": f"{self.base_url}/browse/{mock_key}",
        }

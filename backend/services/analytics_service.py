"""
Analytics Service

Basic aggregation queries for the admin dashboard.
Person 4 will extend this with more sophisticated analytics.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.message import Message
from models.session import Session
from models.ticket import Ticket

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Provides aggregate metrics for the admin dashboard."""

    async def get_overview(self, db: AsyncSession) -> dict:
        """Return high-level metrics for the dashboard.

        Returns a dict compatible with ``schemas.analytics.MetricOverview``.
        """
        total_sessions = (
            await db.execute(select(func.count(Session.id)))
        ).scalar() or 0

        total_messages = (
            await db.execute(
                select(func.count(Message.id)).where(Message.role == "user")
            )
        ).scalar() or 0

        total_tickets = (
            await db.execute(select(func.count(Ticket.id)))
        ).scalar() or 0

        # Average confidence of assistant messages that have a score.
        avg_confidence_row = await db.execute(
            select(func.avg(Message.confidence_score)).where(
                Message.confidence_score.isnot(None),
                Message.role == "assistant",
            )
        )
        avg_confidence = avg_confidence_row.scalar() or 0.0

        # Resolution rate = sessions with status=resolved / total sessions
        resolved_sessions = (
            await db.execute(
                select(func.count(Session.id)).where(Session.status == "resolved")
            )
        ).scalar() or 0

        # Escalation rate = sessions with status=escalated / total sessions
        escalated_sessions = (
            await db.execute(
                select(func.count(Session.id)).where(Session.status == "escalated")
            )
        ).scalar() or 0

        resolution_rate = (
            resolved_sessions / total_sessions if total_sessions else 0.0
        )
        escalation_rate = (
            escalated_sessions / total_sessions if total_sessions else 0.0
        )

        return {
            "total_queries": total_messages,
            "resolution_rate": round(resolution_rate, 4),
            "escalation_rate": round(escalation_rate, 4),
            "avg_confidence_score": round(float(avg_confidence), 4),
            "total_tickets": total_tickets,
            "total_sessions": total_sessions,
        }

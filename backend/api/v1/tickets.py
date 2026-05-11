"""Ticket API endpoints (Admin View)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import DbSession
from schemas.ticket import (
    TicketDetailResponse,
    TicketEscalateRequest,
    TicketEscalateResponse,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
    TicketUpdateResponse,
)
from services.service_factory import get_ticket_service

router = APIRouter()


@router.get(
    "",
    response_model=TicketListResponse,
)
async def list_tickets(
    db: DbSession,
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
) -> TicketListResponse:
    """List tickets with optional status/severity filters."""
    ticket_service = get_ticket_service()
    tickets = await ticket_service.list_tickets(
        db=db, status=status_filter, severity=severity
    )
    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets]
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
)
async def get_ticket(ticket_id: UUID, db: DbSession) -> TicketDetailResponse:
    """Get a single ticket by ID."""
    ticket_service = get_ticket_service()
    ticket = await ticket_service.get_ticket(db, str(ticket_id))
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return TicketDetailResponse(ticket=TicketResponse.model_validate(ticket))


@router.post(
    "/escalate",
    response_model=TicketEscalateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def escalate_ticket(
    body: TicketEscalateRequest,
    db: DbSession,
) -> TicketEscalateResponse:
    """Manually escalate a chat session to a Jira ticket."""
    ticket_service = get_ticket_service()
    try:
        ticket = await ticket_service.create_manual_ticket(
            db=db,
            session_id=str(body.session_id),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return TicketEscalateResponse(
        ticket=TicketResponse.model_validate(ticket),
        jira_key=ticket.jira_issue_key,
    )


@router.put(
    "/{ticket_id}",
    response_model=TicketUpdateResponse,
)
async def update_ticket(
    ticket_id: UUID,
    body: TicketUpdate,
    db: DbSession,
) -> TicketUpdateResponse:
    """Update ticket status or severity."""
    ticket_service = get_ticket_service()
    update_data = body.model_dump(exclude_none=True)
    ticket = await ticket_service.update_ticket(db, str(ticket_id), **update_data)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return TicketUpdateResponse(ticket=TicketResponse.model_validate(ticket))

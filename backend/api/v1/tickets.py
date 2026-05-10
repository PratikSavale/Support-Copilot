from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from schemas.ticket import (
    TicketDetailResponse,
    TicketEscalateRequest,
    TicketEscalateResponse,
    TicketListResponse,
    TicketUpdate,
    TicketUpdateResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=TicketListResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def list_tickets(
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
) -> TicketListResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def get_ticket(ticket_id: UUID) -> TicketDetailResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post(
    "/escalate",
    response_model=TicketEscalateResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def escalate_ticket(_body: TicketEscalateRequest) -> TicketEscalateResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.put(
    "/{ticket_id}",
    response_model=TicketUpdateResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def update_ticket(ticket_id: UUID, _body: TicketUpdate) -> TicketUpdateResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )

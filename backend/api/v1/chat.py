from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, status

from schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={501: {"description": "Not implemented yet"}},
)
async def create_session(
    _: SessionCreate | None = Body(default=None),
) -> SessionResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def send_message(session_id: UUID, _message: ChatRequest) -> ChatResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def list_sessions() -> SessionListResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def get_session(session_id: UUID) -> SessionDetailResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )

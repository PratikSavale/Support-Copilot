from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from schemas.knowledge import (
    KnowledgeSourceCreate,
    KnowledgeSourceCreateAccepted,
    KnowledgeSourceDeleteResponse,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)

router = APIRouter()


@router.post(
    "/sources",
    response_model=KnowledgeSourceCreateAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses={501: {"description": "Not implemented yet"}},
)
async def add_knowledge_source(_body: KnowledgeSourceCreate) -> KnowledgeSourceCreateAccepted:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get(
    "/sources",
    response_model=KnowledgeSourceListResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def list_knowledge_sources() -> KnowledgeSourceListResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.delete(
    "/sources/{source_id}",
    response_model=KnowledgeSourceDeleteResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def delete_knowledge_source(source_id: UUID) -> KnowledgeSourceDeleteResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post(
    "/sources/{source_id}/reindex",
    response_model=KnowledgeSourceResponse,
    responses={501: {"description": "Not implemented yet"}},
)
async def reindex_knowledge_source(source_id: UUID) -> KnowledgeSourceResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )

"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]

# Person 3+: replace with real auth; keep import path stable for downstream tasks.
__all__ = ["DbSession", "get_db"]

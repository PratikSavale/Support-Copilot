from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRoleSchema(str, Enum):
    agent = "agent"
    manager = "manager"
    admin = "admin"


class UserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: EmailStr
    role: UserRoleSchema = UserRoleSchema.agent


class UserCreate(UserBase):
    password: str = Field(..., min_length=1, description="Plain password; hashed server-side later")


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.role import Role


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: Role


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[Role]
    tenant_id: uuid.UUID
    created_at: datetime


class UserList(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int

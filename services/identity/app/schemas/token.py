import uuid

from pydantic import BaseModel

from app.models.role import Role


class TokenPayload(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    roles: list[Role]
    exp: int

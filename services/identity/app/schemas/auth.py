from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    tenant_slug: str
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    tenant_name: str = Field(min_length=1, max_length=255)
    tenant_slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    admin_email: str
    admin_password: str = Field(min_length=8)
    admin_full_name: str = Field(min_length=1, max_length=255)

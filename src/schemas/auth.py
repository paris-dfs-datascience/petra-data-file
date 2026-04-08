from __future__ import annotations

from pydantic import BaseModel


class TokenRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthenticatedUserResponse(BaseModel):
    subject: str
    tenant_id: str
    object_id: str | None = None
    display_name: str | None = None
    preferred_username: str | None = None
    client_app_id: str | None = None
    scopes: list[str] = []

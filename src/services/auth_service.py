from __future__ import annotations

from src.core.config import Settings
from src.core.security import create_access_token
from src.schemas.auth import TokenResponse


class AuthenticationError(Exception):
    pass


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def issue_token(self, email: str, password: str) -> TokenResponse:
        if email != self.settings.APP_ADMIN_EMAIL or password != self.settings.APP_ADMIN_PASSWORD:
            raise AuthenticationError("Invalid credentials.")
        token = create_access_token(subject=email, settings=self.settings)
        return TokenResponse(
            access_token=token,
            expires_in=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

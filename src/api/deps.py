from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import Settings, get_settings
from src.core.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


def get_current_user_email(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings_dep),
) -> str | None:
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials, settings)
        return str(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc

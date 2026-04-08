from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import Settings, get_settings
from src.core.azure_auth import AzureAuthError, AzureUserPrincipal, validate_azure_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


def require_authenticated_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings_dep),
) -> AzureUserPrincipal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        return validate_azure_access_token(credentials.credentials, settings)
    except AzureAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def get_current_user_email(
    principal: AzureUserPrincipal = Depends(require_authenticated_principal),
) -> str | None:
    return principal.preferred_username or principal.subject

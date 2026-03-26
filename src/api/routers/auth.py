from fastapi import APIRouter, Depends

from src.api.deps import get_settings_dep
from src.core.config import Settings
from src.schemas.auth import TokenRequest, TokenResponse
from src.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def issue_token(payload: TokenRequest, settings: Settings = Depends(get_settings_dep)) -> TokenResponse:
    service = AuthService(settings)
    return service.issue_token(email=payload.email, password=payload.password)

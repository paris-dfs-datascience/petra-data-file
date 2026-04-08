from fastapi import APIRouter, Depends

from src.api.deps import require_authenticated_principal
from src.core.azure_auth import AzureUserPrincipal
from src.schemas.auth import AuthenticatedUserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthenticatedUserResponse)
async def read_current_user(
    principal: AzureUserPrincipal = Depends(require_authenticated_principal),
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        subject=principal.subject,
        tenant_id=principal.tenant_id,
        object_id=principal.object_id,
        display_name=principal.display_name,
        preferred_username=principal.preferred_username,
        client_app_id=principal.client_app_id,
        scopes=principal.scopes,
    )

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.request import urlopen

import jwt
from jwt import PyJWKClient

from src.core.config import Settings


class AzureAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class AzureUserPrincipal:
    subject: str
    tenant_id: str
    object_id: str | None
    display_name: str | None
    preferred_username: str | None
    client_app_id: str | None
    scopes: list[str]
    raw_claims: dict[str, Any]


def ensure_azure_auth_configured(settings: Settings) -> None:
    missing_fields = [
        field_name
        for field_name in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_REQUIRED_SCOPE")
        if not getattr(settings, field_name, None)
    ]
    if missing_fields:
        raise RuntimeError(
            "Azure authentication is required but missing configuration: " + ", ".join(missing_fields)
        )


@lru_cache(maxsize=8)
def _fetch_openid_configuration(authority_host: str, tenant_id: str, token_version: str) -> dict[str, Any]:
    version_path = "" if token_version == "1.0" else "/v2.0"
    metadata_url = f"{authority_host.rstrip('/')}/{tenant_id}{version_path}/.well-known/openid-configuration"
    with urlopen(metadata_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache(maxsize=8)
def _get_jwk_client(jwks_uri: str) -> PyJWKClient:
    return PyJWKClient(jwks_uri)


def _extract_scopes(claims: dict[str, Any]) -> list[str]:
    raw_scope_value = str(claims.get("scp", "") or "").strip()
    if not raw_scope_value:
        return []
    return [scope for scope in raw_scope_value.split(" ") if scope]


def _extract_client_app_id(claims: dict[str, Any]) -> str | None:
    for claim_name in ("azp", "appid"):
        value = str(claims.get(claim_name, "") or "").strip()
        if value:
            return value
    return None


def _extract_subject(claims: dict[str, Any]) -> str | None:
    for claim_name in ("oid", "sub"):
        value = str(claims.get(claim_name, "") or "").strip()
        if value:
            return value
    return None


def validate_azure_access_token(token: str, settings: Settings) -> AzureUserPrincipal:
    ensure_azure_auth_configured(settings)

    try:
        unverified_claims = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_nbf": False,
                "verify_iat": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except jwt.PyJWTError as exc:
        raise AzureAuthError("Invalid Azure access token.") from exc

    token_version = str(unverified_claims.get("ver", "") or "")
    if token_version not in settings.AZURE_ACCEPTED_TOKEN_VERSIONS:
        raise AzureAuthError(
            f"Unsupported Azure token version '{token_version or 'unknown'}'. Accepted versions: {', '.join(settings.AZURE_ACCEPTED_TOKEN_VERSIONS)}.",
        )

    tenant_id = str(unverified_claims.get("tid", "") or "")
    if tenant_id != settings.AZURE_TENANT_ID:
        raise AzureAuthError("The token tenant is not allowed.")

    openid_config = _fetch_openid_configuration(
        settings.AZURE_AUTHORITY_HOST,
        settings.AZURE_TENANT_ID or "",
        token_version,
    )
    jwk_client = _get_jwk_client(str(openid_config["jwks_uri"]))

    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=str(openid_config["issuer"]),
            options={
                "require": ["aud", "iss", "exp", "iat", "tid"],
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError as exc:
        raise AzureAuthError("Azure access token validation failed.") from exc

    audience = str(claims.get("aud", "") or "")
    if audience not in settings.azure_expected_audiences:
        raise AzureAuthError("The token audience does not match this API.")

    scopes = _extract_scopes(claims)
    if settings.AZURE_REQUIRED_SCOPE not in scopes:
        raise AzureAuthError("The token is missing the required API scope.", status_code=403)

    client_app_id = _extract_client_app_id(claims)
    if settings.AZURE_ALLOWED_CLIENT_APP_IDS:
        if not client_app_id:
            raise AzureAuthError("The token is missing the client application claim.", status_code=403)
        if client_app_id not in settings.AZURE_ALLOWED_CLIENT_APP_IDS:
            raise AzureAuthError("The calling client application is not allowed.", status_code=403)

    subject = _extract_subject(claims)
    if not subject:
        raise AzureAuthError("The token is missing the subject claim.")

    return AzureUserPrincipal(
        subject=subject,
        tenant_id=tenant_id,
        object_id=str(claims.get("oid", "") or "") or None,
        display_name=str(claims.get("name", "") or "") or None,
        preferred_username=str(claims.get("preferred_username", "") or claims.get("upn", "") or "") or None,
        client_app_id=client_app_id,
        scopes=scopes,
        raw_claims=claims,
    )

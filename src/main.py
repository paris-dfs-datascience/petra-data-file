from __future__ import annotations

from contextlib import asynccontextmanager
import json
from pathlib import Path

import typer
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from src.api.deps import require_authenticated_principal
from src.api.errors import register_exception_handlers
from src.api.middleware import register_middleware
from src.api.routers import auth, health, rules, validations
from src.core.azure_auth import ensure_azure_auth_configured
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.services.validation_service import ValidationService


cli = typer.Typer(help="Petra Vision service CLI")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        ensure_azure_auth_configured(settings)
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        dependencies=[Depends(require_authenticated_principal)],
        lifespan=lifespan,
    )
    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(validations.router, prefix=settings.API_PREFIX)
    app.include_router(rules.router, prefix=settings.API_PREFIX)

    # Deprecated: the legacy built-in UI under src/ui is no longer mounted by the backend.
    # The supported operator UI now lives in the separate React frontend under frontend/.
    # ENABLE_UI is kept only for backward-compatible configuration parsing and is ignored here.
    @app.get("/")
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "service": settings.APP_NAME,
                "docs": None,
                "api_prefix": settings.API_PREFIX,
                "runtime_mode": "ephemeral",
                "persistence": "disabled",
                "ui_enabled": False,
                "legacy_ui_deprecated": True,
                "authentication": "microsoft-entra-id",
            }
        )

    return app


app = create_app()


def _run_pipeline(pdf_path: str) -> dict:
    service = ValidationService()
    return service.validate_document(pdf_path=pdf_path)


@cli.command("validate")
def cli_validate(
    pdf: str = typer.Option(..., help="Path to the PDF"),
    out: str | None = typer.Option(None, help="Where to write the extraction JSON. If omitted, prints JSON to stdout."),
) -> None:
    data = _run_pipeline(pdf_path=pdf)
    if out is None:
        typer.echo(json.dumps(data, indent=2))
        return

    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


if __name__ == "__main__":
    cli()

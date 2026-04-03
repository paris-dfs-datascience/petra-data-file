from __future__ import annotations

import json
from pathlib import Path

import typer
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.errors import register_exception_handlers
from src.api.middleware import register_middleware
from src.api.routers import auth, health, rules, validations
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.services.validation_service import ValidationService


cli = typer.Typer(help="Petra Vision service CLI")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.APP_NAME)
    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(validations.router, prefix=settings.API_PREFIX)
    app.include_router(rules.router, prefix=settings.API_PREFIX)

    if settings.ENABLE_UI:
        from src.ui.router import build_ui_router

        ui_static_dir = Path(__file__).resolve().parent / "ui" / "static"
        app.mount("/ui-static", StaticFiles(directory=str(ui_static_dir)), name="ui-static")
        app.include_router(build_ui_router(settings))

    if not settings.ENABLE_UI:
        @app.get("/")
        async def root() -> JSONResponse:
            return JSONResponse(
                content={
                    "service": settings.APP_NAME,
                    "docs": "/docs",
                    "api_prefix": settings.API_PREFIX,
                    "runtime_mode": "ephemeral",
                    "persistence": "disabled",
                    "ui_enabled": settings.ENABLE_UI,
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

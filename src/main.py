from __future__ import annotations

import json
from pathlib import Path

import typer
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.errors import register_exception_handlers
from src.api.middleware import register_middleware
from src.api.routers import auth, documents, health, rules, validations
from src.core.config import get_settings, load_app_yaml, project_paths
from src.core.database import init_database
from src.core.logging import configure_logging
from src.services.validation_service import ValidationService


cli = typer.Typer(help="Petra Vision service CLI")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    init_database()
    app = FastAPI(title=settings.APP_NAME)
    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(documents.router, prefix=settings.API_PREFIX)
    app.include_router(validations.router, prefix=settings.API_PREFIX)
    app.include_router(rules.router, prefix=settings.API_PREFIX)

    public_dir = Path(settings.PUBLIC_DIR)
    public_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

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
                    "storage_backend": settings.STORAGE_BACKEND,
                    "database_backend": settings.DATABASE_BACKEND,
                    "ui_enabled": settings.ENABLE_UI,
                }
            )

    return app


app = create_app()


def _run_pipeline(pdf_path: str) -> dict:
    init_database()
    service = ValidationService()
    return service.validate_document(pdf_path=pdf_path)


@cli.command("validate")
def cli_validate(
    pdf: str = typer.Option(..., help="Path to the PDF"),
    out: str | None = typer.Option(None, help="Where to write the extraction JSON. Default under data/reports"),
) -> None:
    data = _run_pipeline(pdf_path=pdf)
    if out is None:
        app_cfg = load_app_yaml()
        paths = project_paths(app_cfg)
        Path(paths["reports"]).mkdir(parents=True, exist_ok=True)
        out = str(paths["reports"] / f"{data['document_id']}.json")
    Path(out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


if __name__ == "__main__":
    cli()

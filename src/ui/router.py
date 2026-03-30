from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.core.config import Settings


TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"
STATIC_DIR = Path(__file__).resolve().parent / "static"
APP_JS_PATH = STATIC_DIR / "app.js"
APP_CSS_PATH = STATIC_DIR / "app.css"


def build_ui_router(settings: Settings) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get("/", response_class=HTMLResponse)
    async def ui_home() -> HTMLResponse:
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
        asset_version = str(
            int(
                max(
                    TEMPLATE_PATH.stat().st_mtime,
                    APP_JS_PATH.stat().st_mtime,
                    APP_CSS_PATH.stat().st_mtime,
                )
            )
        )
        html = html.replace("{{ app_name }}", settings.APP_NAME)
        html = html.replace("{{ api_prefix }}", settings.API_PREFIX)
        html = html.replace("{{ storage_backend }}", settings.STORAGE_BACKEND)
        html = html.replace("{{ database_backend }}", settings.DATABASE_BACKEND)
        html = html.replace("{{ ui_assets_version }}", asset_version)
        return HTMLResponse(content=html)

    return router

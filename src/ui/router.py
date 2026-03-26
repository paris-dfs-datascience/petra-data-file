from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.core.config import Settings


TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"


def build_ui_router(settings: Settings) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get("/", response_class=HTMLResponse)
    async def ui_home() -> HTMLResponse:
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
        html = html.replace("{{ app_name }}", settings.APP_NAME)
        html = html.replace("{{ api_prefix }}", settings.API_PREFIX)
        html = html.replace("{{ storage_backend }}", settings.STORAGE_BACKEND)
        html = html.replace("{{ database_backend }}", settings.DATABASE_BACKEND)
        return HTMLResponse(content=html)

    return router

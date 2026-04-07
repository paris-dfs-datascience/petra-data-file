from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings


logger = logging.getLogger("petra.api")


def register_middleware(app: FastAPI) -> None:
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.API_ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
        return response

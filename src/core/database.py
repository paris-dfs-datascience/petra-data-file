from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from threading import Lock

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateColumn

from src.core.config import build_database_url, get_settings
from src.db.base import Base


settings = get_settings()
database_url = build_database_url(settings)

engine_kwargs: dict = {"future": True}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
_schema_lock = Lock()
_schema_initialized = False


def _import_models() -> None:
    import src.models.document  # noqa: F401
    import src.models.feedback  # noqa: F401
    import src.models.rule  # noqa: F401
    import src.models.user  # noqa: F401
    import src.models.validation  # noqa: F401


def _apply_additive_schema_updates() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if not existing_tables:
        return

    with engine.begin() as connection:
        live_inspector = inspect(connection)
        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in live_inspector.get_columns(table_name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                compiled_column = str(CreateColumn(column).compile(dialect=engine.dialect)).strip()
                if not compiled_column or "PRIMARY KEY" in compiled_column.upper():
                    continue

                try:
                    connection.exec_driver_sql(f'ALTER TABLE "{table_name}" ADD COLUMN {compiled_column}')
                except Exception:
                    continue


def _recover_interrupted_runs() -> None:
    from src.models.validation import ValidationRun

    with SessionLocal() as db:
        interrupted_runs = list(
            db.scalars(select(ValidationRun).where(ValidationRun.status.in_(("queued", "running")))).all()
        )
        if not interrupted_runs:
            return

        for run in interrupted_runs:
            run.status = "failed"
            run.message = "Validation interrupted by process restart."
            if not run.error_message:
                run.error_message = "The application restarted before this validation finished."
            run.finished_at = datetime.utcnow()

        db.commit()


def init_database() -> None:
    global _schema_initialized
    if _schema_initialized:
        return

    with _schema_lock:
        if _schema_initialized:
            return
        url = make_url(database_url)
        if url.drivername.startswith("sqlite") and url.database:
            Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        _import_models()
        Base.metadata.create_all(bind=engine)
        _apply_additive_schema_updates()
        _recover_interrupted_runs()
        _schema_initialized = True


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

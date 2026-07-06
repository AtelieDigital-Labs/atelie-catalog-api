from sqlalchemy import String, Boolean, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import table_registry
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column
)
from datetime import datetime


@mapped_as_dataclass(table_registry, kw_only=True)
class LogOutbox():
    __tablename__ = "outbox_logs"

    outbox_id:  Mapped[int] = mapped_column(primary_key=True, autoincrement=True)   
    log_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool]  = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
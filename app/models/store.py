from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    registry,
    relationship,
)

# Cria a instância do registro
table_registry = registry()


@mapped_as_dataclass(table_registry)
class StoreCategory:
    __tablename__ = 'store_categories'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(150), unique=True)

    stores: Mapped[list['Store']] = relationship(
        init=False, back_populates='category', cascade='all, delete-orphan'
    )


@mapped_as_dataclass(table_registry)
class Store:
    __tablename__ = 'stores'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    artisan_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey('store_categories.id'), default=None
    )
    category: Mapped[StoreCategory] = relationship(
        init=False, back_populates='stores'
    )
    image: Mapped[str | None] = mapped_column(String(255), default=None)
    banner: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

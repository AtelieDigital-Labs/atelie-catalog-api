from decimal import Decimal
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, DateTime, func
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    query_expression,
    relationship,
)
from datetime import datetime, timedelta, timezone
from app.models.base import table_registry

class VisibilityMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, init=False, default=False)


@mapped_as_dataclass(table_registry, kw_only=True)
class Product(VisibilityMixin):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.id'))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    is_favorite: Mapped[bool] = query_expression()
    variations: Mapped[List['ProductVariation']] = relationship(
        init=False,
        back_populates='product',
        cascade='all, delete-orphan',
    )


    created_at: Mapped[datetime] = mapped_column(DateTime, init=False,server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, init=False,server_default=func.now(), onupdate=func.now())


@mapped_as_dataclass(table_registry, kw_only=True)
class ProductVariation(VisibilityMixin):
    __tablename__ = 'product_variations'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    weight: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    length: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    width: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    height: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    sku: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        default=None,
    )

    stock: Mapped[int] = mapped_column(default=0)
    color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )
    size: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    product: Mapped['Product'] = relationship(
        init=False,
        back_populates='variations',
    )

    images: Mapped[List['ProductImage']] = relationship(
        init=False,
        back_populates='variation',
        cascade='all, delete-orphan',
    )


@mapped_as_dataclass(table_registry, kw_only=True)
class ProductImage(VisibilityMixin):
    __tablename__ = 'product_images'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    url: Mapped[str] = mapped_column(String(255))
    variation_id: Mapped[int] = mapped_column(
        ForeignKey('product_variations.id')
    )

    is_primary: Mapped[bool] = mapped_column(default=False)

    variation: Mapped['ProductVariation'] = relationship(
        init=False,
        back_populates='images',
    )

class ReservationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELED = "canceled"

def get_default_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=15)

@mapped_as_dataclass(table_registry, kw_only=True)
class StockReservation:
    __tablename__ = 'stock_reservation'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    
    product_variant_id: Mapped[int] = mapped_column(
        ForeignKey('product_variations.id', ondelete='CASCADE') 
    )

    order_id: Mapped[int] = mapped_column(index=True)
    
    quantity: Mapped[int] = mapped_column()
    
    # default_factory garante que a função execute CADA VEZ que um novo objeto for criado
    expire: Mapped[datetime] = mapped_column(
        default_factory=get_default_expiration
    )
    
    status: Mapped[ReservationStatus] = mapped_column(
        default=ReservationStatus.PENDING
    )
    


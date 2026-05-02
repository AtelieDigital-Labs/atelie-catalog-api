from decimal import Decimal
from typing import Optional, List

from sqlalchemy import ForeignKey, String, Numeric, Boolean
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    mapped_as_dataclass,
)

from app.models.base import table_registry


@mapped_as_dataclass(table_registry, kw_only=True)
class Product:
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.id'))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    variations: Mapped[List['ProductVariation']] = relationship(
        init=False,
        back_populates='product',
        cascade='all, delete-orphan',
    )


@mapped_as_dataclass(table_registry, kw_only=True)
class ProductVariation:
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
class ProductImage:
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
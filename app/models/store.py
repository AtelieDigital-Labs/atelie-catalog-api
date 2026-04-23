from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, mapped_as_dataclass
from app.core.database import table_registry

@mapped_as_dataclass(table_registry=table_registry)
class StoreCategory:
    __tablename__ = 'store_categories'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(150))
    
  
    stores: Mapped[list['Store']] = relationship(
        init=False, back_populates='category', cascade='all, delete-orphan'
    )

@mapped_as_dataclass(table_registry=table_registry)
class Store:
    __tablename__ = 'stores'


    id: Mapped[int] = mapped_column(primary_key=True, init=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    category_id: Mapped[int | None] = mapped_column(ForeignKey('store_categories.id'), default=None)
    category: Mapped[StoreCategory] = relationship(init=False, back_populates='stores')
    images: Mapped[list['StoreImage']] = relationship(init=False, back_populates='store')

    # Imagens (URLs/Caminhos)
    image: Mapped[str | None] = mapped_column(String(255), default=None)
    banner: Mapped[str | None] = mapped_column(String(255), default=None)

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

@mapped_as_dataclass(table_registry=table_registry)
class StoreImage:
    __tablename__ = 'store_images'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.id'))
    image: Mapped[str] = mapped_column(String(255))
    
    store: Mapped[Store] = relationship(init=False, back_populates='images')
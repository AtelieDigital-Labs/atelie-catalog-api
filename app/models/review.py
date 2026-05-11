from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column

from app.models.base import table_registry


@mapped_as_dataclass(table_registry, kw_only=True)
class Review:
    __tablename__ = 'reviews'

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'product_id',
            name='uq_review_user_product',
        ),
    )

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id', ondelete='CASCADE')
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:

    @staticmethod
    async def get_by_user_and_product(
        session: AsyncSession,
        user_id: str,
        product_id: int,
    ) -> Review | None:
        result = await session.execute(
            select(Review).where(
                Review.user_id == user_id,
                Review.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_product(
        session: AsyncSession,
        product_id: int,
    ) -> list[Review]:
        result = await session.execute(
            select(Review).where(Review.product_id == product_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_average_rating(
        session: AsyncSession,
        product_id: int,
    ) -> float:
        result = await session.execute(
            select(func.avg(Review.rating)).where(
                Review.product_id == product_id
            )
        )
        average = result.scalar_one_or_none()
        return round(float(average), 1) if average else 0.0

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: str,
        product_id: int,
        rating: int,
        comment: str | None,
    ) -> Review:
        review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=comment,
        )
        session.add(review)
        await session.commit()
        await session.refresh(review)
        return review
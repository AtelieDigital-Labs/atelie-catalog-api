from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.orders import OrdersClient
from app.models.product import Product
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewList, ReviewPublic, ReviewSchema


class ReviewService:

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: str,
        product_id: int,
        payload: ReviewSchema,
    ) -> ReviewPublic:
        product = await session.get(Product, product_id)

        if not product or not product.is_active:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        is_valid_purchase = await OrdersClient.validate_purchase(
            user_id, product_id
        )

        if not is_valid_purchase:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You can only review products you have purchased',
            )

        existing = await ReviewRepository.get_by_user_and_product(
            session, user_id, product_id
        )

        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='You have already reviewed this product',
            )

        return await ReviewRepository.create(
            session,
            user_id=user_id,
            product_id=product_id,
            rating=payload.rating,
            comment=payload.comment,
        )

    @staticmethod
    async def list_by_product(
        session: AsyncSession,
        product_id: int,
    ) -> ReviewList:
        product = await session.get(Product, product_id)

        if not product or not product.is_active:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        reviews = await ReviewRepository.list_by_product(session, product_id)
        average = await ReviewRepository.get_average_rating(
            session, product_id
        )

        return {
            'reviews': reviews,
            'total': len(reviews),
            'average_rating': average,
        }
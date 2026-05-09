from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.favorite import FavoriteRepository
from app.schemas.favorite import FavoriteList, FavoritePublic


class FavoriteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = FavoriteRepository(session)

    async def add(self, user_id: str, product_id: int) -> FavoritePublic:
        product = await self.session.get(Product, product_id)

        if not product or not product.is_active:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        existing = await self.repository.get_by_user_and_product(
            user_id, product_id
        )

        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Product already favorited',
            )

        return await self.repository.create(user_id, product_id)

    async def remove(self, user_id: str, product_id: int) -> None:
        favorite = await self.repository.get_by_user_and_product(
            user_id, product_id
        )

        if not favorite:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Favorite not found',
            )

        await self.repository.delete(favorite)

    async def list_by_user(self, user_id: str) -> FavoriteList:
        favorites = await self.repository.get_all_by_user(user_id)
        return {'favorites': favorites}

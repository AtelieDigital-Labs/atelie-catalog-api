from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_product(
        self,
        user_id: str,
        product_id: int,
    ) -> Favorite | None:
        result = await self.session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: str) -> list[Favorite]:
        result = await self.session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(self, user_id: str, product_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, product_id=product_id)
        self.session.add(favorite)
        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def delete(self, favorite: Favorite) -> None:
        await self.session.delete(favorite)
        await self.session.commit()
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.product import Product, ProductVariation
from app.models.store import Address, Store, StoreCategory


class CategoryRepository:
    @staticmethod
    async def get_by_name(
        session: AsyncSession,
        name: str,
    ) -> StoreCategory | None:
        result = await session.execute(
            select(StoreCategory).where(StoreCategory.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        category_id: int,
    ) -> StoreCategory | None:
        return await session.get(StoreCategory, category_id)

    @staticmethod
    async def list_all(session: AsyncSession) -> list[StoreCategory]:
        result = await session.execute(select(StoreCategory))
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
    ) -> StoreCategory:
        db_category = StoreCategory(name=name)
        session.add(db_category)
        await session.commit()
        await session.refresh(db_category)
        return db_category

    @staticmethod
    async def update(
        session: AsyncSession,
        db_category: StoreCategory,
        data: dict,
    ) -> StoreCategory:
        for key, value in data.items():
            setattr(db_category, key, value)

        session.add(db_category)
        await session.commit()
        await session.refresh(db_category)
        return db_category


class StoreRepository:
    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        store_id: int,
    ) -> Store | None:
        result = await session.execute(
            select(Store)
            .where(Store.id == store_id)
            .options(
                joinedload(Store.category),
                joinedload(Store.address),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id_and_owner(
        session: AsyncSession,
        store_id: int,
        user_id: str,
    ) -> Store | None:
        result = await session.execute(
            select(Store)
            .where(Store.id == store_id, Store.artisan_id == user_id)
            .options(
                joinedload(Store.category),
                joinedload(Store.address),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Store]:
        result = await session.execute(
            select(Store)
            .options(joinedload(Store.category), joinedload(Store.address))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        payload,
        user_id: str,
    ) -> Store:
        db_store = Store(
            name=payload.name,
            description=payload.description,
            category_id=payload.category_id,
            image=payload.image,
            banner=payload.banner,
            artisan_id=user_id,
        )

        db_address = Address(
            street=payload.address.street,
            number=payload.address.number,
            neighborhood=payload.address.neighborhood,
            city=payload.address.city,
            state=payload.address.state,
            zip_code=payload.address.zip_code,
            complement=payload.address.complement,
        )

        db_store.address = db_address
        session.add(db_store)
        await session.commit()

        result = await session.execute(
            select(Store)
            .where(Store.id == db_store.id)
            .options(joinedload(Store.category), joinedload(Store.address))
        )
        return result.scalar_one()

    @staticmethod
    async def update(
        session: AsyncSession,
        db_store: Store,
        update_data: dict,
    ) -> Store:
        if 'address' in update_data:
            address_data = update_data.pop('address')
            if db_store.address:
                for key, value in address_data.items():
                    setattr(db_store.address, key, value)
            else:
                new_address = Address(**address_data)
                new_address.store_id = db_store.id
                session.add(new_address)
                db_store.address = new_address

        for key, value in update_data.items():
            setattr(db_store, key, value)

        session.add(db_store)
        await session.commit()

        result = await session.execute(
            select(Store)
            .where(Store.id == db_store.id)
            .options(joinedload(Store.category), joinedload(Store.address))
        )
        return result.scalar_one()

    @staticmethod
    async def get_active_products(
        session: AsyncSession,
        store_id: int,
    ) -> list[Product]:
        products_query = (
            select(Product)
            .where(
                Product.store_id == store_id,
                Product.is_active,
            )
            .options(
                joinedload(Product.variations).joinedload(
                    ProductVariation.images
                )
            )
        )

        products_result = await session.execute(products_query)
        products = products_result.unique().scalars().all()

        active_products = []
        for product in products:
            active_variations = [v for v in product.variations if v.stock > 0]
            if active_variations:
                product.variations = active_variations
                active_products.append(product)

        return active_products

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from infra.messaging.publishers.store_created import publisher_store_created
from app.repositories.store import CategoryRepository, StoreRepository
from app.schemas.store import (
    CategoryList,
    CategoryPublic,
    CategorySchema,
    CategoryUpdate,
    StoreList,
    StorePublic,
    StoreSchema,
    StoreUpdate,
    StoreWithProductsPublic,
)


class CategoryService:
    @staticmethod
    async def create(
        session: AsyncSession,
        payload: CategorySchema,
    ) -> CategoryPublic:
        existing = await CategoryRepository.get_by_name(session, payload.name)

        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Esta categoria já está cadastrada',
            )

        return await CategoryRepository.create(session, payload.name)

    @staticmethod
    async def list_all(session: AsyncSession) -> CategoryList:
        categories = await CategoryRepository.list_all(session)
        return {'categories': categories}

    @staticmethod
    async def update(
        session: AsyncSession,
        category_id: int,
        payload: CategoryUpdate,
    ) -> CategoryPublic:
        db_category = await CategoryRepository.get_by_id(session, category_id)

        if not db_category:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Categoria não encontrada',
            )

        if payload.name:
            existing = await CategoryRepository.get_by_name(
                session, payload.name
            )
            if existing:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail='Este nome de categoria já está em uso',
                )

        data = payload.model_dump(exclude_unset=True)
        return await CategoryRepository.update(session, db_category, data)


class StoreService:
    @staticmethod
    async def create(
        session: AsyncSession,
        payload: StoreSchema,
        user_id: str,
    ) -> StorePublic:

        existing = await StoreRepository.get_by_artisan_id(session, user_id)

        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='You already have a store',
            )

        category = await CategoryRepository.get_by_id(
            session, payload.category_id
        )

        if not category:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Categoria informada não existe',
            )
        store = await StoreRepository.create(session, payload, user_id)

        
        from infra.messaging.events.store_created import StoreCreatedEvent
        event = StoreCreatedEvent(
            store_id=str(store.id),
            artisan_id=store.artisan_id,
            pix_key=payload.pix_key
        )
        await publisher_store_created(event)
        
        return store

    
    # async def publish_messaging(data: dict):
    #     from ..messaging.publishers.store_created import publisher_store_created
    #     from ..messaging.events.store_created import StoreCreatedEvent
    #     await broker.publish(

    #     )

    @staticmethod
    async def list_all(
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> StoreList:
        stores = await StoreRepository.list_all(session, limit, offset)
        return {'stores': stores}

    @staticmethod
    async def update_my_store(
        session: AsyncSession,
        payload: StoreUpdate,
        user_id: str,
    ) -> StorePublic:
        store = await StoreRepository.get_by_artisan_id(session, user_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='You do not have a store yet',
            )

        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
        return await StoreRepository.update(session, store, update_data)

    @staticmethod
    async def get_with_products(
        session: AsyncSession,
        store_id: int,
    ) -> StoreWithProductsPublic:
        store = await StoreRepository.get_by_id(session, store_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Store not found',
            )

        active_products = await StoreRepository.get_active_products(
            session, store_id
        )

        return StoreWithProductsPublic(
            id=store.id,
            artisan_id=store.artisan_id,
            name=store.name,
            description=store.description,
            category=store.category,
            image=store.image,
            banner=store.banner,
            address=store.address,
            created_at=store.created_at,
            updated_at=store.updated_at,
            products=active_products,
        )

    @staticmethod
    async def get_my_store(
        session: AsyncSession,
        user_id: str,
    ) -> StorePublic:
        store = await StoreRepository.get_by_artisan_id(session, user_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='You do not have a store yet',
            )

        return store

    @staticmethod
    async def get_artisan(
        session: AsyncSession,
        store_id: int,
    ):
        store = await StoreRepository.get_by_id(session, store_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Store not found',
            )

        return {
            'store_id': store.id,
            'artisan_id': store.artisan_id,
        }

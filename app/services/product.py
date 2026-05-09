from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store
from app.repositories.product import ProductRepository
from app.schemas.product import FilterProduct, ProductList, ProductSchema, ProductUpdate


class ProductService:

    @staticmethod
    async def create(
        session: AsyncSession,
        payload: ProductSchema,
        user_id: str,
    ):
        store = await session.get(Store, payload.store_id)

        if not store or store.artisan_id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Loja não encontrada ou sem permissão',
            )

        try:
            return await ProductRepository.create(
                session,
                name=payload.name,
                description=payload.description,
                store_id=payload.store_id,
                variations_data=payload.variations,
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='SKU já cadastrado',
            )

    @staticmethod
    async def list_products(
        session: AsyncSession,
        filters: FilterProduct,
    ) -> ProductList:
        products = await ProductRepository.list_with_filters(session, filters)
        return {'products': products}

    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: int):
        product = await ProductRepository.get_by_id(session, product_id)

        if not product or not product.is_active:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        return product

    @staticmethod
    async def update(
        session: AsyncSession,
        product_id: int,
        payload: ProductUpdate,
        user_id: str,
    ):
        product = await ProductRepository.get_by_id(session, product_id)

        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        store = await session.get(Store, product.store_id)

        if not store or store.artisan_id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        data = payload.model_dump(exclude_unset=True)

        try:
            return await ProductRepository.update(session, product, data)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='SKU already exists',
            )

    @staticmethod
    async def delete(
        session: AsyncSession,
        product_id: int,
        user_id: str,
    ):
        product = await ProductRepository.get_by_id(session, product_id)

        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )

        store = await session.get(Store, product.store_id)

        if not store or store.artisan_id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        await ProductRepository.delete(session, product)
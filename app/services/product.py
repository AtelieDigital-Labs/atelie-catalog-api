from http import HTTPStatus

from app.models.product import ReservationStatus
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store
from app.repositories.product import ProductRepository, StockReservationRepository
from app.repositories.store import StoreRepository
from app.schemas.product import (
    FilterProduct,
    ProductList,
    ProductSchema,
    ProductUpdate,
    ProductVariationDetail,
)


class ProductService:
    @staticmethod
    async def create(
        session: AsyncSession,
        payload: ProductSchema,
        user_id: str,
    ):
        # busca a loja do artesão automaticamente
        store = await StoreRepository.get_by_artisan_id(session, user_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='You do not have a store yet',
            )

        try:
            return await ProductRepository.create(
                session,
                name=payload.name,
                description=payload.description,
                store_id=store.id,
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
    async def get_variation_by_id(
        session: AsyncSession,
        variation_id: int,
    ):
        variation = await ProductRepository.get_variation_by_id(
            session, variation_id
        )

        if not variation:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Variation not found',
            )

        return ProductVariationDetail(
            id=variation.id,
            product_id=variation.product_id,
            store_id=variation.product.store_id,  # ← pega do produto
            price=variation.price,
            stock=variation.stock,
            weight=float(variation.weight),
            height=float(variation.height),
            width=float(variation.width),
            length=float(variation.length),
            sku=variation.sku,
            color=variation.color,
            size=variation.size,
        )

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

    @staticmethod
    async def reserve(session: AsyncSession, data):
        try:
            variant = await ProductRepository.get_variation_by_id(session, data.product_variant_id)
            if not variant:
                raise Exception("Product not Found")
            if variant.stock < data.quantity:
                raise Exception("Estoque insuficiente")
            variant.stock -= data.quantity

            reserve = await StockReservationRepository.create(
                session=session,
                data=data
            )

            await session.commit()
            await session.refresh(reserve)
            return reserve
        except Exception:
            await session.rollback()

    @staticmethod
    async def confirm_reserve(session: AsyncSession, data):
        try:
            reserve = await StockReservationRepository.get_by_order_id(session, order_id=data.order_id)
            if reserve.status != ReservationStatus.PENDING:
                return reserve
            reserve = await StockReservationRepository.change_status(session, reserve=reserve, status=ReservationStatus.CONFIRMED)

            await session.commit()
            return await session.refresh(reserve)
        except Exception:
            await session.rollback()

    @staticmethod
    async def expire_reserve(session: AsyncSession, data):
        try:
            variant = await ProductRepository.get_variation_by_id(session, data.product_variant_id)
            if not variant:
                raise Exception("Product not Found")
            reserve = await StockReservationRepository.get_by_id(session, reserve_id=data.reserve_id)

            if reserve.status != ReservationStatus.PENDING:
                return reserve

            reserve = await StockReservationRepository.change_status(session, reserve=reserve, status=ReservationStatus.EXPIRED)
            variant.stock += reserve.quantity

            await session.commit()
            return await session.refresh(reserve)
        except Exception:
            await session.rollback()


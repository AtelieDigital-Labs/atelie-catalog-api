from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_session
from app.core.security import CurrentUser
from app.models.product import Product, ProductImage, ProductVariation
from app.models.store import Store
from app.schemas.product import (
    ProductPublic,
    ProductSchema,
)

router = APIRouter(prefix='/products', tags=['products'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post('/', response_model=ProductPublic, status_code=HTTPStatus.CREATED)
async def create_product(
    payload: ProductSchema,
    session: Session,
    user: CurrentUser,
):
    store = await session.get(Store, payload.store_id)

    if not store or store.artisan_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Loja não encontrada ou sem permissão',
        )

    try:
        db_product = Product(
            name=payload.name,
            description=payload.description,
            store_id=payload.store_id,
        )

        session.add(db_product)
        await session.flush()

        for variation_data in payload.variations:
            db_variation = ProductVariation(
                product_id=db_product.id,
                price=variation_data.price,
                weight=variation_data.weight,
                length=variation_data.length,
                width=variation_data.width,
                height=variation_data.height,
                sku=variation_data.sku,
                stock=variation_data.stock,
                color=variation_data.color,
                size=variation_data.size,
            )

            session.add(db_variation)
            await session.flush()  

            for image_data in variation_data.images:
                db_image = ProductImage(
                    variation_id=db_variation.id,
                    url=image_data.url,
                    is_primary=image_data.is_primary,
                )
                session.add(db_image)

        await session.commit()

    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='SKU já cadastrado',
        )

    result = await session.execute(
        select(Product)
        .where(Product.id == db_product.id)
        .options(
            joinedload(Product.variations).joinedload(ProductVariation.images)
        )
    )

    return result.unique().scalar_one()

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
    FilterProduct,
    ProductList,
    ProductPublic,
    ProductSchema,
    ProductUpdate,
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


@router.get('/', response_model=ProductList)
async def list_products(
    session: Session,
    filters: Annotated[FilterProduct, Depends()],
):
    query = select(Product).options(
        joinedload(Product.variations).joinedload(ProductVariation.images)
    )

    if filters.name:
        query = query.where(Product.name.ilike(f'%{filters.name}%'))

    if filters.store_id:
        query = query.where(Product.store_id == filters.store_id)

    query = query.limit(filters.limit).offset(filters.offset)

    result = await session.execute(query)
    products = result.unique().scalars().all()

    return {'products': products}


@router.get('/{product_id}', response_model=ProductPublic)
async def get_product(product_id: int, session: Session):
    query = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            joinedload(Product.variations).joinedload(ProductVariation.images)
        )
    )

    result = await session.execute(query)
    product = result.unique().scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Product not found',
        )

    return product


# app/api/routes/product.py


def _update_image(
    db_variation: ProductVariation,
    img_data: dict,
) -> None:
    existing_images = {img.id: img for img in db_variation.images}
    img_id = img_data.get('id')

    if img_id and img_id in existing_images:
        img = existing_images[img_id]
        img.url = img_data.get('url', img.url)
        img.is_primary = img_data.get('is_primary', img.is_primary)
    else:
        db_variation.images.append(
            ProductImage(
                url=img_data['url'],
                is_primary=img_data.get('is_primary', False),
                variation_id=db_variation.id,
            )
        )


def _build_variation(
    product_id: int,
    var_data: dict,
) -> ProductVariation:
    new_variation = ProductVariation(
        product_id=product_id,
        price=var_data['price'],
        weight=var_data['weight'],
        length=var_data['length'],
        width=var_data['width'],
        height=var_data['height'],
        stock=var_data['stock'],
        sku=var_data.get('sku'),
        color=var_data.get('color'),
        size=var_data.get('size'),
    )

    new_variation.images = [
        ProductImage(
            url=img['url'],
            is_primary=img.get('is_primary', False),
            variation_id=None,
        )
        for img in var_data.get('images', [])
    ]

    return new_variation


def _process_variations(
    db_product: Product,
    variations_data: list,
) -> list:
    existing_variations = {v.id: v for v in db_product.variations}
    new_variations = []

    for var_data in variations_data:
        var_id = var_data.get('id')

        if var_id and var_id in existing_variations:
            db_variation = existing_variations[var_id]

            for key, value in var_data.items():
                if key not in {'id', 'images'}:
                    setattr(db_variation, key, value)

            for img_data in var_data.get('images', []):
                _update_image(db_variation, img_data)

            new_variations.append(db_variation)
        else:
            new_variations.append(_build_variation(db_product.id, var_data))

    return new_variations


@router.patch('/{product_id}', response_model=ProductPublic)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    user: CurrentUser,
    session: Session,
):
    result = await session.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            joinedload(Product.variations).joinedload(ProductVariation.images)
        )
    )

    db_product = result.unique().scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Product not found',
        )

    store = await session.get(Store, db_product.store_id)

    if not store or store.artisan_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Not enough permissions',
        )

    data = payload.model_dump(exclude_unset=True)

    for key, value in data.items():
        if key != 'variations':
            setattr(db_product, key, value)

    if 'variations' in data:
        db_product.variations = _process_variations(
            db_product, data['variations']
        )

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='SKU already exists',
        )

    result = await session.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            joinedload(Product.variations).joinedload(ProductVariation.images)
        )
    )

    return result.unique().scalar_one()

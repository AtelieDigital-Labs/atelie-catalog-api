from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.product import Product, ProductImage, ProductVariation
from app.models.store import Store
from app.schemas.product import FilterProduct
from infra.messaging.events.order_create import OrderCreatedEvent
from ..models.product import ReservationStatus, StockReservation
from app.models import product

class ProductRepository:
    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        product_id: int,
    ) -> Product | None:
        result = await session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                joinedload(Product.variations).joinedload(
                    ProductVariation.images
                )
            )
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_variation_by_id(
        session: AsyncSession,
        variation_id: int,
    ) -> ProductVariation | None:
        result = await session.execute(
            select(ProductVariation)
            .where(ProductVariation.id == variation_id)
            .options(joinedload(ProductVariation.product))
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def list_with_filters(
        session: AsyncSession,
        filters: FilterProduct,
    ) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_active)
            .options(
                joinedload(Product.variations).joinedload(
                    ProductVariation.images
                )
            )
        )

        if filters.q:
            query = query.where(Product.name.ilike(f'%{filters.q}%'))

        if filters.category_id:
            query = query.join(Store).where(
                Store.category_id == filters.category_id
            )

        if filters.min_price:
            query = query.where(
                Product.variations.any(
                    ProductVariation.price >= filters.min_price
                )
            )

        if filters.max_price:
            query = query.where(
                Product.variations.any(
                    ProductVariation.price <= filters.max_price
                )
            )

        if filters.sort == 'price_asc':
            min_price_subquery = (
                select(
                    ProductVariation.product_id,
                    func.min(ProductVariation.price).label('min_price'),
                )
                .group_by(ProductVariation.product_id)
                .subquery()
            )

            query = query.outerjoin(
                min_price_subquery,
                Product.id == min_price_subquery.c.product_id,
            ).order_by(asc(min_price_subquery.c.min_price))

        elif filters.sort == 'newest':
            query = query.order_by(Product.id.desc())

        query = query.limit(filters.limit).offset(filters.offset)

        result = await session.execute(query)
        return list(result.unique().scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        description: str,
        store_id: int,
        variations_data: list,
    ) -> Product:
        db_product = Product(
            name=name,
            description=description,
            store_id=store_id,
        )

        session.add(db_product)
        await session.flush()

        for variation_data in variations_data:
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

        result = await session.execute(
            select(Product)
            .where(Product.id == db_product.id)
            .options(
                joinedload(Product.variations).joinedload(
                    ProductVariation.images
                )
            )
        )

        return result.unique().scalar_one()

    @staticmethod
    async def update(
        session: AsyncSession,
        db_product: Product,
        data: dict,
    ) -> Product:
        for key, value in data.items():
            if key != 'variations':
                setattr(db_product, key, value)

        if 'variations' in data:
            db_product.variations = _process_variations(
                db_product, data['variations']
            )

        await session.commit()

        result = await session.execute(
            select(Product)
            .where(Product.id == db_product.id)
            .options(
                joinedload(Product.variations).joinedload(
                    ProductVariation.images
                )
            )
        )

        return result.unique().scalar_one()

    @staticmethod
    async def delete(session: AsyncSession, product: Product) -> None:
        await session.delete(product)
        await session.commit()

class StockReservationRepository:
    @staticmethod
    async def create(session: AsyncSession, data: OrderCreatedEvent):
        reserve = StockReservation(**data.model_dump())
        session.add(reserve)
        
        return reserve
    
    @staticmethod
    async def get_by_id(session: AsyncSession, reserve_id):
        return await session.get(StockReservation, id=reserve_id)
    
    @staticmethod
    async def get_by_order_id(session: AsyncSession, order_id):
        return await session.get(StockReservation, order_id=order_id)

    @staticmethod
    async def change_status(session: AsyncSession, status: ReservationStatus, reserve: StockReservation):
        reserve.status = status
        session.add(reserve)

        return reserve
    


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

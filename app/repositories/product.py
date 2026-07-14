from operator import and_

from sqlalchemy import case
from sqlalchemy import asc, func, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload, query, with_expression
from app.models.favorite import Favorite
from app.models.product import Product, ProductImage, ProductVariation
from app.models.store import Store
from app.schemas.product import FilterProduct
from infra.messaging.events.order_create import OrderCreatedEvent
from ..models.product import ReservationStatus, StockReservation
from app.models import product
import uuid
from datetime import datetime, timezone
from app.models.outbox import LogOutbox
from app.core.context import current_user_id
from app.core.logger import setup_trigger_logger


logger = setup_trigger_logger()

class ProductRepository:
    @staticmethod
    def _apply_favorites_and_options(stmt, user=None):
        """
        Método auxiliar para aplicar de forma consistente o mapeamento de favoritos 
        e o carregamento das variações/imagens em qualquer query de Produto.
        """
        FavoriteAlias = aliased(Favorite)
        if user:
            stmt = (
                stmt.outerjoin(
                    FavoriteAlias,
                    and_(
                        FavoriteAlias.product_id == Product.id,
                        FavoriteAlias.user_id == user.id,
                    ),
                )
                .options(
                    with_expression(
                        Product.is_favorite,
                        case(
                            (FavoriteAlias.id.is_not(None), True),
                            else_=False,
                        ),
                    )
                )
            )
        
        # Carregamento ansioso (Eager Loading) padrão para variações e imagens
        return stmt.options(
            joinedload(Product.variations).joinedload(
                ProductVariation.images
            )
        )

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        product_id: int,
        user=None,  # Adicionado suporte ao usuário
    ) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        stmt = ProductRepository._apply_favorites_and_options(stmt, user)
        
        result = await session.execute(stmt)
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
        user=None,  # Definido valor padrão None
    ) -> list[Product]:
        stmt = select(Product)
        stmt = ProductRepository._apply_favorites_and_options(stmt, user)

        if filters.q:
            stmt = stmt.where(Product.name.ilike(f'%{filters.q}%'))

        if filters.category_id:
            stmt = stmt.join(Store).where(
                Store.category_id == filters.category_id
            )

        if filters.min_price:
            stmt = stmt.where(
                Product.variations.any(
                    ProductVariation.price >= filters.min_price
                )
            )

        if filters.max_price:
            stmt = stmt.where(
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

            stmt = stmt.outerjoin(
                min_price_subquery,
                Product.id == min_price_subquery.c.product_id,
            ).order_by(asc(min_price_subquery.c.min_price))

        elif filters.sort == 'newest':
            stmt = stmt.order_by(Product.id.desc())

        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result = await session.execute(stmt)
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

        await session.commit()

        stmt = select(Product).where(Product.id == db_product.id)
        stmt = ProductRepository._apply_favorites_and_options(stmt, None)

        result = await session.execute(stmt)
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

        stmt = select(Product).where(Product.id == db_product.id)
        stmt = ProductRepository._apply_favorites_and_options(stmt, None)
 
        result = await session.execute(stmt)
        return result.unique().scalar_one()

    @staticmethod
    async def delete(session: AsyncSession, product_id: int) -> None:
        actor = str(current_user_id.get())

        await session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(is_deleted=True)
        )

        await session.execute(
            update(ProductVariation)
            .where(ProductVariation.product_id == product_id)
            .values(is_deleted=True)
        )

        await session.execute(
            update(ProductImage)
            .where(
                ProductImage.variation_id.in_(
                    select(ProductVariation.id).where(ProductVariation.product_id == product_id)
                )
            )
            .values(is_deleted=True)
        )

        log_payload = {
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "microservice": "Catalog",
            "actor": {
                "user_id": actor
            },
            "action": "SOFT DELETE",
            "resource": "Product",
            "resource_id": product_id,
            "changes": {
                "status": {
                    "old_value": None,
                    "new_value": "DELETED" 
                }
            },
            "reason": "Deleção lógica de um produto e suas cascatas"
        }

        await session.execute(
            insert(LogOutbox).values(
                log_id=log_payload["log_id"],
                aggregate_type="Product",
                aggregate_id=str(product_id), 
                payload=log_payload,
                processed=False
            )
        )

        await session.commit()

        logger.info(f"[SOFT DELETE] Transação concluída e outbox salvo. Produto {product_id} deletado.")

    @staticmethod
    async def get_by_ids(
        session: AsyncSession, 
        list_ids: list[int],
        user=None,  # Adicionado suporte ao usuário
    ) -> list[Product]:
        print(list_ids)
        stmt = select(Product).where(Product.id.in_(list_ids))
        stmt = ProductRepository._apply_favorites_and_options(stmt, user)
        
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    @staticmethod
    async def get_by_store_id(
        session: AsyncSession,
        store_id: int,
        user=None,  # Adicionado suporte ao usuário
    ) -> list[Product]:
        stmt = select(Product).where(Product.store_id == store_id)
        stmt = ProductRepository._apply_favorites_and_options(stmt, user)

        result = await session.execute(stmt)
        return result.unique().scalars().all()

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
    
class ProductImageRepository:
    @staticmethod
    async def create(session: AsyncSession, variation_id, url: str):
        image = ProductImage(
            variation_id=variation_id,
            url=url
        )
        session.add(image)
        await session.flush()
        await session.refresh(image)

        return image

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

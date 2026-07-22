from http import HTTPStatus

from app.models.product import ReservationStatus
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store
from app.repositories.product import (
    ProductImageRepository,
    ProductRepository,
    StockReservationRepository,
)
from app.repositories.store import StoreRepository
from app.schemas.product import (
    FilterProduct,
    ProductList,
    ProductSchema,
    ProductUpdate,
    ProductVariationDetail,
)
from app.services.storage import StorageService


class ProductService:
    @staticmethod
    async def create(
        session: AsyncSession,
        payload: ProductSchema,
        images: list[UploadFile],
        image_variant_ids: list[str],
        user_id: str,
    ):
        store = await StoreRepository.get_by_artisan_id(session, user_id)

        if not store:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='You do not have a store yet',
            )

        if len(images) != len(image_variant_ids):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Each image must have a variant id.',
            )

        try:
            product = await ProductRepository.create(
                session=session,
                name=payload.name,
                description=payload.description,
                store_id=store.id,
                variations_data=payload.variations,
            )

            # Mapeia temp_id -> variante criada
            variations_by_temp_id = {
                payload_variation.temp_id: db_variation
                for payload_variation, db_variation in zip(
                    payload.variations,
                    product.variations,
                    strict=True,
                )
            }

            for image, temp_id in zip(images, image_variant_ids, strict=True):
                variation = variations_by_temp_id.get(temp_id)

                if variation is None:
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail=f"Variation '{temp_id}' not found.",
                    )

                image_url = StorageService.upload(
                    file=image,
                    directory=f'products/{product.id}',
                )

                await ProductImageRepository.create(
                    session=session,
                    variation_id=variation.id,
                    url=image_url,
                )

            await session.commit()

        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='SKU já cadastrado',
            )

        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def list_products(
        session: AsyncSession, filters: FilterProduct, user
    ) -> ProductList:
        products = await ProductRepository.list_with_filters(
            session, filters, user
        )
        for product in products:
            for variation in product.variations:
                for image in variation.images:
                    image.url = StorageService.presigned_url(image.url)

        return {'products': products}

    @staticmethod
    async def products_favorites_by_ids(
        session: AsyncSession,
        list_ids: list[int],
        user
    ) -> ProductList:
        products = await ProductRepository.get_by_ids(session, list_ids, user)
        for product in products:
            for variation in product.variations:
                for image in variation.images:
                    image.url = StorageService.presigned_url(image.url)
        return {'products': products}

    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: int, user):
        product = await ProductRepository.get_by_id(session, product_id, user)

        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Product not found',
            )
        for variation in product.variations:
            for image in variation.images:
                image.url = StorageService.presigned_url(image.url)
        return product

    @staticmethod
    async def get_variation_by_id(
        session: AsyncSession,
        variation_id: int,
    ):
        variation = await ProductRepository.get_variation_by_id(
            session, variation_id
        )

        if not variation or not variation.product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Variation or Product not found',
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
        images: list[UploadFile],
        image_variant_ids: list[str],
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

        if len(images) != len(image_variant_ids):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Each image must have a variant id.',
            )

        # 1. Prepara os dados cadastrais isolando as imagens
        data = payload.model_dump(exclude_unset=True)
        
        # 🔥 CRITICAL: Removemos 'images' do dict enviado ao repositório para evitar 
        # que o SQLAlchemy limpe ou corrompa a relação existente durante o update genérico.
        if "variations" in data:
            for var_data in data["variations"]:
                var_data.pop("images", None)

        try:
            # 2. Atualiza apenas os dados cadastrais do produto e variações
            updated_product = await ProductRepository.update(session, product, data)

            # 3. Mapeamento inteligente de temp_id -> Variação salva
            payload_variations = payload.variations or []
            
            payload_variations_with_id = {
                v.id: v for v in payload_variations if v.id is not None
            }
            payload_variations_new = [
                v for v in payload_variations if v.id is None
            ]

            variations_by_temp_id = {}
            db_variations_new = []

            for db_var in updated_product.variations:
                if db_var.id in payload_variations_with_id:
                    # Usamos o payload original (que ainda tem as imagens preservadas)
                    payload_var = payload_variations_with_id[db_var.id]
                    variations_by_temp_id[payload_var.temp_id] = db_var

                    # ─────────────────────────────────────────────────────────
                    # 🔥 GESTÃO CIRÚRGICA DE EXCLUSÃO DE IMAGENS
                    # ─────────────────────────────────────────────────────────
                    payload_images = getattr(payload_var, "images", None)
                    if payload_images is not None:
                        # Identifica apenas os IDs que o front-end quer MANTER
                        payload_image_ids = {
                            img.id for img in payload_images if img.id is not None
                        }

                        # Compara as imagens do banco: se não veio na lista do front, exclui do banco
                        for db_image in list(db_var.images):
                            if db_image.id not in payload_image_ids:
                                await session.delete(db_image)
                    # ─────────────────────────────────────────────────────────

                else:
                    db_variations_new.append(db_var)

            # Associa as novas variações na ordem exata de criação
            for payload_var, db_var in zip(payload_variations_new, db_variations_new):
                variations_by_temp_id[payload_var.temp_id] = db_var

            # 4. Faz o upload das mídias novas e as associa no banco
            for image, temp_id in zip(images, image_variant_ids, strict=True):
                variation = variations_by_temp_id.get(temp_id)

                if variation is None:
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail=f"Variation '{temp_id}' not found.",
                    )

                image_url = StorageService.upload(
                    file=image,
                    directory=f'products/{updated_product.id}',
                )

                await ProductImageRepository.create(
                    session=session,
                    variation_id=variation.id,
                    url=image_url,
                )

            await session.commit()
            
            # Atualiza o objeto para que as deleções reflitam no retorno da API
            await session.refresh(updated_product)
            return updated_product

        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='SKU already exists',
            )
        except Exception:
            await session.rollback()
            raise Exception


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

        await ProductRepository.delete(session, product_id)

    @staticmethod
    async def reserve(session: AsyncSession, data):
        try:
            variant = await ProductRepository.get_variation_by_id(
                session, data.product_variant_id
            )
            if not variant:
                raise Exception('Product not Found')
            if variant.stock < data.quantity:
                raise Exception('Estoque insuficiente')
            variant.stock -= data.quantity

            reserve = await StockReservationRepository.create(
                session=session, data=data
            )

            await session.commit()
            await session.refresh(reserve)
            return reserve
        except Exception:
            await session.rollback()

    @staticmethod
    async def confirm_reserve(session: AsyncSession, data):
        try:
            reserve = await StockReservationRepository.get_by_order_id(
                session, order_id=data.order_id
            )
            if reserve.status != ReservationStatus.PENDING:
                return reserve
            reserve = await StockReservationRepository.change_status(
                session, reserve=reserve, status=ReservationStatus.CONFIRMED
            )

            await session.commit()
            return await session.refresh(reserve)
        except Exception:
            await session.rollback()

    @staticmethod
    async def expire_reserve(session: AsyncSession, data):
        try:
            variant = await ProductRepository.get_variation_by_id(
                session, data.product_variant_id
            )
            if not variant:
                raise Exception('Product not Found')
            reserve = await StockReservationRepository.get_by_id(
                session, reserve_id=data.reserve_id
            )

            if reserve.status != ReservationStatus.PENDING:
                return reserve

            reserve = await StockReservationRepository.change_status(
                session, reserve=reserve, status=ReservationStatus.EXPIRED
            )
            variant.stock += reserve.quantity

            await session.commit()
            return await session.refresh(reserve)
        except Exception:
            await session.rollback()

    @staticmethod
    async def get_by_store_id(session: AsyncSession, store_id: int):
        products = await ProductRepository.get_by_store_id(session, store_id)

        for product in products:
            for variation in product.variations:
                for image in variation.images:
                    image.url = StorageService.presigned_url(image.url)

        return products

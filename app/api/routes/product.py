import json

from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import AuthUser, CurrentUser, CurrentUserOrNone, get_current_user_none
from app.schemas.product import (
    FilterProduct,
    ProductList,
    ProductPublic,
    ProductSchema,
    ProductUpdate,
    ProductVariationDetail,
)
from app.services.product import ProductService

router = APIRouter(prefix='/products', tags=['products'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post('/', status_code=HTTPStatus.CREATED)
async def create_product(
    session: Session,
    user: CurrentUser,
    payload: Annotated[str, Form()],
    images: list[UploadFile] = File(default=[]),          # Permitir lista vazia como padrão
    image_variant_ids: list[str] = Form(default=[])
):
    data = ProductSchema.model_validate(json.loads(payload))
    await ProductService.create(session, data, images, image_variant_ids ,user.id)
    return "Created"


@router.get('/', response_model=ProductList)
async def list_products(
    session: Session,
    filters: Annotated[FilterProduct, Depends()],
    user: CurrentUserOrNone,
):
    return await ProductService.list_products(session, filters, user)


@router.post('/me/favorites', response_model=ProductList)
async def get_me_products_favorites(
    session: Session,
    list_ids: list[int],
    user: CurrentUserOrNone
):
    return await ProductService.products_favorites_by_ids(
        session=session,
        list_ids=list_ids,
        user=user
    )


@router.get(
    '/variations/{variation_id}',
    response_model=ProductVariationDetail,
)
async def get_variation(variation_id: int, session: Session):
    return await ProductService.get_variation_by_id(session, variation_id)


@router.get('/{product_id}', response_model=ProductPublic)
async def get_product(product_id: int, session: Session, user: CurrentUserOrNone):
    return await ProductService.get_by_id(session, product_id, user)


@router.patch('/{product_id}', response_model=ProductPublic)
async def update_product(
    user: CurrentUser,
    session: Session,
    product_id: int,
    payload: Annotated[str, Form()],
    images: list[UploadFile] = File(default=[]),          
    image_variant_ids: list[str] = Form(default=[])
):
    data = ProductUpdate.model_validate(json.loads(payload))
    return await ProductService.update(session, product_id, data, images, image_variant_ids, user.id)


@router.delete('/{product_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_product(
    product_id: int,
    user: CurrentUser,
    session: Session,
):
    await ProductService.delete(session, product_id, user.id)

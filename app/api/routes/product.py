from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser
from app.schemas.product import (
    FilterProduct,
    ProductList,
    ProductPublic,
    ProductSchema,
    ProductUpdate,
)
from app.services.product import ProductService

router = APIRouter(prefix='/products', tags=['products'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post('/', response_model=ProductPublic, status_code=HTTPStatus.CREATED)
async def create_product(
    payload: ProductSchema,
    session: Session,
    user: CurrentUser,
):
    return await ProductService.create(session, payload, user.id)


@router.get('/', response_model=ProductList)
async def list_products(
    session: Session,
    filters: Annotated[FilterProduct, Depends()],
):
    return await ProductService.list_products(session, filters)


@router.get('/{product_id}', response_model=ProductPublic)
async def get_product(product_id: int, session: Session):
    return await ProductService.get_by_id(session, product_id)


@router.patch('/{product_id}', response_model=ProductPublic)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    user: CurrentUser,
    session: Session,
):
    return await ProductService.update(session, product_id, payload, user.id)


@router.delete('/{product_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_product(
    product_id: int,
    user: CurrentUser,
    session: Session,
):
    await ProductService.delete(session, product_id, user.id)

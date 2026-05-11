from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser
from app.schemas.review import (
    ReviewList,
    ReviewPublic,
    ReviewSchema,
    ReviewUpdate,
)
from app.services.review import ReviewService

router = APIRouter(prefix='/reviews', tags=['reviews'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    '/{product_id}',
    response_model=ReviewPublic,
    status_code=HTTPStatus.CREATED,
)
async def create_review(
    product_id: int,
    payload: ReviewSchema,
    user: CurrentUser,
    session: Session,
):
    return await ReviewService.create(session, user.id, product_id, payload)


@router.get('/{product_id}', response_model=ReviewList)
async def list_reviews(product_id: int, session: Session):
    return await ReviewService.list_by_product(session, product_id)


@router.delete('/{product_id}', status_code=HTTPStatus.NO_CONTENT)
async def delete_review(
    product_id: int,
    user: CurrentUser,
    session: Session,
):
    await ReviewService.delete(session, user.id, product_id)


@router.patch('/{product_id}', response_model=ReviewPublic)
async def update_review(
    product_id: int,
    payload: ReviewUpdate,
    user: CurrentUser,
    session: Session,
):
    return await ReviewService.update(session, user.id, product_id, payload)

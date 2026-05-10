from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser
from app.schemas.review import ReviewList, ReviewPublic, ReviewSchema
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
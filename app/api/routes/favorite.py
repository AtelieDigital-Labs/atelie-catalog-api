from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser
from app.schemas.favorite import FavoriteList, FavoritePublic
from app.services.favorite import FavoriteService

router = APIRouter(prefix='/favorites', tags=['favorites'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    '/{product_id}',
    response_model=FavoritePublic,
    status_code=HTTPStatus.CREATED,
)
async def add_favorite(
    product_id: int,
    user: CurrentUser,
    session: Session,
):
    service = FavoriteService(session)
    return await service.add(user.id, product_id)


@router.delete('/{product_id}', status_code=HTTPStatus.NO_CONTENT)
async def remove_favorite(
    product_id: int,
    user: CurrentUser,
    session: Session,
):
    service = FavoriteService(session)
    await service.remove(user.id, product_id)


@router.get('/', response_model=FavoriteList)
async def list_favorites(
    user: CurrentUser,
    session: Session,
):
    service = FavoriteService(session)
    return await service.list_by_user(user.id)
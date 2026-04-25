from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_session
from app.core.security import CurrentUser
from app.models.store import Store, StoreCategory
from app.schemas.store import (
    CategoryList,
    CategoryPublic,
    CategorySchema,
    StoreList,
    StorePublic,
    StoreSchema,
)

router = APIRouter(prefix='/stores', tags=['stores'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    '/categories',
    response_model=CategoryPublic,
    status_code=HTTPStatus.CREATED,
)
async def create_category(
    category: CategorySchema, session: Session, user: CurrentUser
):

    query = select(StoreCategory).where(StoreCategory.name == category.name)
    result = await session.execute(query)
    if result.scalar():
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta categoria já está cadastrada',
        )

    db_category = StoreCategory(name=category.name)
    session.add(db_category)
    await session.commit()
    await session.refresh(db_category)
    return db_category


@router.get('/categories', response_model=CategoryList)
async def list_categories(session: Session):
    query = select(StoreCategory)
    result = await session.execute(query)
    categories = result.scalars().all()
    return {'categories': categories}


@router.post('/', response_model=StorePublic, status_code=HTTPStatus.CREATED)
async def create_store(
    payload: StoreSchema, session: Session, user: CurrentUser
):

    category = await session.get(StoreCategory, payload.category_id)
    if not category:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Categoria informada não existe',
        )

    db_store = Store(
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        image=payload.image,
        banner=payload.banner,
        artisan_id=user.id,
    )

    session.add(db_store)
    await session.commit()

    query = (
        select(Store)
        .where(Store.id == db_store.id)
        .options(joinedload(Store.category))
    )
    result = await session.execute(query)
    return result.scalar_one()


@router.get('/', response_model=StoreList)
async def list_stores(session: Session, limit: int = 10, offset: int = 0):

    query = (
        select(Store)
        .options(joinedload(Store.category))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    stores = result.scalars().all()

    return {'stores': stores}

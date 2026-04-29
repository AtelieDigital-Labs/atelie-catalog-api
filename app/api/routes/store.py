from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_session
from app.core.security import CurrentUser
from app.models.store import Address, Store, StoreCategory
from app.schemas.store import (
    CategoryList,
    CategoryPublic,
    CategorySchema,
    CategoryUpdate,
    StoreList,
    StorePublic,
    StoreSchema,
    StoreUpdate,
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

    existing_category = result.scalar_one_or_none()

    if existing_category:
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

    db_address = Address(
        street=payload.address.street,
        number=payload.address.number,
        neighborhood=payload.address.neighborhood,
        city=payload.address.city,
        state=payload.address.state,
        zip_code=payload.address.zip_code,
        complement=payload.address.complement,
    )

    db_store.address = db_address

    session.add(db_store)
    await session.commit()

    query = (
        select(Store)
        .where(Store.id == db_store.id)
        .options(joinedload(Store.category), joinedload(Store.address))
    )
    result = await session.execute(query)
    return result.scalar_one()


@router.get('/', response_model=StoreList)
async def list_stores(session: Session, limit: int = 10, offset: int = 0):

    query = (
        select(Store)
        .options(joinedload(Store.category), joinedload(Store.address))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    stores = result.scalars().all()

    return {'stores': stores}


@router.patch('/{store_id}', response_model=StorePublic)
async def update_store(
    store_id: int, payload: StoreUpdate, user: CurrentUser, session: Session
):

    query = (
        select(Store)
        .where(Store.id == store_id, Store.artisan_id == user.id)
        .options(joinedload(Store.category), joinedload(Store.address))
    )

    result = await session.execute(query)
    db_store = result.scalar_one_or_none()

    if not db_store:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Loja não encontrada ou você não possui permissão para '
            'editá-la',
        )

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

    if 'address' in update_data:
        address_data = update_data.pop('address')
        if db_store.address:
            for key, value in address_data.items():
                setattr(db_store.address, key, value)
        else:
            new_address = Address(**address_data)
            new_address.store_id = db_store.id

            session.add(new_address)
            db_store.address = new_address

    # Atualização dos campos da Loja
    for key, value in update_data.items():
        setattr(db_store, key, value)

    session.add(db_store)
    await session.commit()

    result = await session.execute(query)
    return result.scalar_one()


@router.patch('/categories/{category_id}', response_model=CategoryPublic)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    user: CurrentUser,
    session: Session,
):

    db_category = await session.get(StoreCategory, category_id)

    if not db_category:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Categoria não encontrada'
        )

    if payload.name:
        query_check = select(StoreCategory).where(
            StoreCategory.name == payload.name
        )
        result_check = await session.execute(query_check)
        if result_check.scalar():
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Este nome de categoria já está em uso',
            )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)

    session.add(db_category)
    await session.commit()
    await session.refresh(db_category)

    return db_category

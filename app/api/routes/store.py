from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.minio import S3Client
from app.core.security import CurrentUser
from app.schemas.product import ProductPublic
from app.schemas.store import (
    CategoryList,
    CategoryPublic,
    CategorySchema,
    CategoryUpdate,
    StoreArtisanPublic,
    StoreList,
    StorePublic,
    StoreSchema,
    StoreUpdate,
    StoreWithProductsPublic,
)
from app.services.product import ProductService
from app.services.store import CategoryService, StoreService

router = APIRouter(prefix='/stores', tags=['stores'])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    '/categories',
    response_model=CategoryPublic,
    status_code=HTTPStatus.CREATED,
)
async def create_category(
    category: CategorySchema,
    session: Session,
    user: CurrentUser,
):
    return await CategoryService.create(session, category)


@router.get('/categories', response_model=CategoryList)
async def list_categories(session: Session):
    return await CategoryService.list_all(session)


@router.post('/', response_model=StorePublic, status_code=HTTPStatus.CREATED)
async def create_store(
    image: UploadFile,
    banner: UploadFile,
    session: Session,
    storage: S3Client,
    user: CurrentUser,
    payload: StoreSchema = Depends(StoreSchema.as_form),
):
    return await StoreService.create(
        session=session,
        payload=payload,
        image=image,
        banner=banner,
        user_id=user.id,
        storage=storage
    )


@router.get('/', response_model=StoreList)
async def list_stores(
    session: Session,
    limit: int = 10,
    offset: int = 0,
):
    return await StoreService.list_all(session, limit, offset)


@router.patch('/me', response_model=StorePublic)
async def update_my_store(
    user: CurrentUser,
    session: Session,
    image: UploadFile | None = None,
    banner: UploadFile | None = None,
    payload: StoreUpdate = Depends(StoreUpdate.as_form)
):
    return await StoreService.update_my_store(
        session=session,
        payload=payload,
        image=image, 
        banner=banner,
        user_id=user.id)


@router.patch('/categories/{category_id}', response_model=CategoryPublic)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    user: CurrentUser,
    session: Session,
):
    return await CategoryService.update(session, category_id, payload)


@router.get('/me', response_model=StorePublic)
async def get_my_store(user: CurrentUser, session: Session):
    return await StoreService.get_my_store(session, user.id)


@router.get(
    '/{store_id}/artisan',
    response_model=StoreArtisanPublic,
)
async def get_store_artisan(
    store_id: int,
    session: Session,
):
    return await StoreService.get_artisan(session, store_id)


@router.get('/{store_id}', response_model=StoreWithProductsPublic)
async def get_store(store_id: int, session: Session):
    return await StoreService.get_with_products(session, store_id)

@router.get("/me/products/", response_model=list[ProductPublic])
async def get_me_store_products(user: CurrentUser, session: Session):
    return await StoreService.get_products(session, user.id)
    
@router.get("/{store_id}/products/", response_model=list[ProductPublic])
async def get_store_products(store_id: int, session: Session):
    return await ProductService.get_by_store_id(session, store_id)

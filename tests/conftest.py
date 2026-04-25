import factory
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.database import get_session
from app.main import app
from app.models.store import Store, StoreCategory, table_registry

DATABASE_URL = 'sqlite+aiosqlite:///:memory:'

engine = create_async_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


class CategoryFactory(factory.Factory):
    class Meta:
        model = StoreCategory

    name = factory.Sequence(lambda n: f'Categoria {n}')


@pytest_asyncio.fixture
async def category(session: AsyncSession):

    category = CategoryFactory()
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@pytest_asyncio.fixture
async def user():
    class MockUser:
        id = '1'  # Mesmo ID que da store
        email = 'artesao@teste.com'
        username = 'artesao_fake'
        token = 'fake-token-artesao-1'  # O teste vai ler isso aqui

    return MockUser()


# 2. Fixture de outro Usuário (Para testar o erro 403 Forbidden)
@pytest_asyncio.fixture
async def other_user():
    class MockOtherUser:
        id = '999'  # ID diferente para falhar na validação de dono
        email = 'outro@teste.com'
        username = 'outro_artesao'
        token = 'fake-token-outro'

    return MockOtherUser()


@pytest_asyncio.fixture
async def client(session):
    async def _get_test_db():
        yield session

    app.dependency_overrides[get_session] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


class StoreFactory(factory.Factory):
    class Meta:
        model = Store

    name = factory.Sequence(lambda n: f'Loja Teste {n}')
    description = 'Uma descrição de teste para a loja'
    image = 'http://image.com/foto.jpg'
    banner = 'http://image.com/banner.jpg'
    # category_id e artisan_id serão preenchidos pela fixture abaixo


@pytest_asyncio.fixture
async def store(session: AsyncSession, category):
    # Cria uma loja automaticamente vinculada à categoria e ao artesão fake
    store = StoreFactory(category_id=category.id, artisan_id='1')
    session.add(store)
    await session.commit()
    await session.refresh(store)
    return store

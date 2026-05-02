import factory
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import joinedload
from testcontainers.postgres import PostgresContainer

from app.core.database import get_session
from app.main import app
from app.models.store import Address, Store, StoreCategory, table_registry


@pytest.fixture(scope='session')
def engine():
    # Removendo o driver='psycopg' daqui para termos controle total da URL
    with PostgresContainer('postgres:16') as postgres:
        # Pegamos os dados crus do container
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(postgres.port)
        user = postgres.username
        password = postgres.password
        db = postgres.dbname

        # Montamos a URL manualmente no formato correto para o SQLAlchemy async
        url = f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db}'

        _engine = create_async_engine(url)
        yield _engine


# Recebe a 'engine' do container e limpa os dados após cada teste.
@pytest_asyncio.fixture
async def session(engine):
    # Cria as tabelas antes do teste
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    # Cria a sessão para o teste usar
    TestingSessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with TestingSessionLocal() as session:
        yield session

    # Limpa as tabelas após o teste (Teardown)
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
        id = '1'
        email = 'artesao@teste.com'
        username = 'artesao_fake'
        token = 'fake-token-artesao-1'

    return MockUser()


@pytest_asyncio.fixture
async def other_user():
    class MockOtherUser:
        id = '999'
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


class AddressFactory(factory.Factory):
    class Meta:
        model = Address

    street = 'Rua de Teste'
    number = 123
    neighborhood = 'Bairro Central'
    city = 'Cidade Teste'
    state = 'RN'
    zip_code = '59000-000'


@pytest_asyncio.fixture
async def store(session: AsyncSession, category):

    store = StoreFactory(category_id=category.id, artisan_id='1')
    address = AddressFactory()
    store.address = address
    session.add(store)

    await session.commit()

    query = (
        select(Store)
        .where(Store.id == store.id)
        .options(joinedload(Store.category), joinedload(Store.address))
    )
    result = await session.execute(query)
    return result.scalar_one()

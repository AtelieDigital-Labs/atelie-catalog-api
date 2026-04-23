from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import registry
from app.core.config import Settings


table_registry = registry()


engine = create_async_engine(Settings().DATABASE_URL)


SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session():
    async with SessionLocal() as session:
        yield session
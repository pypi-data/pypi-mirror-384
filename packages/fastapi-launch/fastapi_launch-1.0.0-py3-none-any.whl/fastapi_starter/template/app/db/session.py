import logging
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.lib.config import settings

logger = logging.getLogger("uvicorn")

DATABASE_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}"


connect_args = {}
if settings.DB_HOST != "localhost":
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(settings.SSL_CERT_PATH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = True
    connect_args = {"ssl": ssl_context}


async_engine = create_async_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args=connect_args,
)


AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    await async_engine.dispose()
    logger.info("DB: Database closed")

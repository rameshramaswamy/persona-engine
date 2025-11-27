from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

# In prod, this URL comes from Env: postgresql+asyncpg://user:pass@db/persona
DATABASE_URL = getattr(settings, "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/persona")

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Declarative Base
Base = declarative_base()
# -----------------------------------------------------------
# ✅ Database Configuration
# -----------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root@localhost:3306/tw_mgmt"
)

# Create Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True for debugging queries
    future=True,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# -----------------------------------------------------------
# ✅ FastAPI Dependency
# -----------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a new async database session for each request.
    Ensures session cleanup after use.
    """
    async with AsyncSessionLocal() as session:
        yield session

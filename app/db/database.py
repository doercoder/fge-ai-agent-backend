from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

# URL de conexión (asegurarse de usar el +asyncpg)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5435/momostenango")

# Crear el engine asíncrono
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Crear la sesión asíncrona
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Función opcional para crear las tablas
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_pgvector_index():
    sql = text("""
        CREATE INDEX IF NOT EXISTS idx_mcpdocument_embedding_pg 
        ON mcpdocument 
        USING hnsw (embedding_pg vector_cosine_ops);
    """)
    async with async_session() as session:
        await session.execute(sql)
        await session.commit()



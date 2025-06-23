import asyncio
import os
from dotenv import load_dotenv
from blacksheep import Application
from hypercorn.asyncio import serve
from hypercorn.config import Config
from app.api.agent_routes import setup_routes
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.db.database import engine
from app.db.database import create_pgvector_index  

# Cargar .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

# Crear motor async con SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL")
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False)

# Crear app BlackSheep
app = Application()
setup_routes(app)

# Crear tablas (solo si no existen)
@app.on_start
async def on_start():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await create_pgvector_index()
    print("✅ Base de datos inicializada y pgvector index asegurado.")


@app.on_stop
async def on_stop():
    # Aquí podrías cerrar el engine si necesitas limpieza manual
    pass

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{os.getenv('APP_HOST', '127.0.0.1')}:{os.getenv('APP_PORT', '8000')}"]
    asyncio.run(serve(app, config))

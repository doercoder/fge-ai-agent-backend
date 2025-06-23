import databases
import sqlalchemy
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5435/momostenango")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

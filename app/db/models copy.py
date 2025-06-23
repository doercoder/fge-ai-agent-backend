from ormar import Model, Integer, String, Text, LargeBinary
from app.db.database import metadata, database

class Session(Model):
    class Meta:
        tablename = "sessions"
        metadata = metadata
        database = database

    id: int = Integer(primary_key=True)
    session_id: str = String(max_length=100)
    prompt: str = Text()
    reply: str = Text()

class Document(Model):
    class Meta:
        tablename = "documents"
        metadata = metadata
        database = database

    id: int = Integer(primary_key=True)
    title: str = String(max_length=255)
    content: str = Text()
    embedding: bytes = LargeBinary(max_length=100000, nullable=True)

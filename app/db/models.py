from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from typing import Optional, List

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    embedding: Optional[bytes] = Field(default=None)

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, index=True)
    session_id: str
    prompt: str
    reply: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class McpDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content: str
    embedding: Optional[bytes] = Field(default=None)  # serializado con pickle o vector PgVector
    created_at: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(default="root")
    embedding_pg: Optional[List[float]] = Field(default=None, sa_column=Column(Vector(1536)))


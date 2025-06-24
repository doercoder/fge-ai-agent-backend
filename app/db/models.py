from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from pgvector.sqlalchemy import Vector


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

class LatencyLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    endpoint: str
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PotholeReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tipo: str
    ubicacion: str
    prompt_original: str
    filename: Optional[str] = None
    etiquetas: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

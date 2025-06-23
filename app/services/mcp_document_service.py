import pickle
from app.db.database import async_session
from app.db.models import McpDocument
from app.services.embedding_service import generate_embedding

async def save_mcp_document(filename: str, content: str, embedding: list[float]):
    embedding_bytes = pickle.dumps(embedding)

    doc = McpDocument(
        filename=filename,
        content=content,
        embedding=embedding_bytes
    )

    async with async_session() as session:
        session.add(doc)
        await session.commit()



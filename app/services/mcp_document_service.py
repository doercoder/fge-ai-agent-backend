import pickle
from app.db.models import McpDocument
from app.db.database import async_session

async def save_mcp_document(filename: str, content: str, embedding: list[float], path: str = "root"):
    pickled = pickle.dumps(embedding)

    new_doc = McpDocument(
        filename=filename,
        content=content,
        embedding=pickled,
        embedding_pg=embedding,
        path=path
    )

    async with async_session() as session:
        session.add(new_doc)
        await session.commit()

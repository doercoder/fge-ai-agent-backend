# document_routes.py
from blacksheep import post, get, Request, Response
from blacksheep.contents import Content
from app.db.models import Document
from app.db.database import async_session
from sqlmodel import select
from app.services.embedding_service import generate_embedding
import json
import pickle

@post("/documents")
async def create_document(request: Request) -> Response:
    body = await request.json()
    title = body.get("title", "")
    content = body.get("content", "")

    embedding = generate_embedding(content)
    embedding_bytes = pickle.dumps(embedding)
    new_doc = Document(title=title, content=content, embedding=embedding_bytes)

    async with async_session() as session:
        session.add(new_doc)
        await session.commit()
        await session.refresh(new_doc)

        doc_dict = new_doc.model_dump()
        if new_doc.embedding:
            doc_dict["embedding"] = pickle.loads(new_doc.embedding)

        return Response(
            201,
            content=Content(b"application/json", json.dumps(doc_dict).encode("utf-8"))
        )

@get("/documents")
async def search_documents(request: Request) -> Response:
    async with async_session() as session:
        result = await session.execute(select(Document))
        documents = result.scalars().all()

        serialized = []
        for doc in documents:
            doc_dict = doc.model_dump()
            if doc.embedding:
                doc_dict["embedding"] = pickle.loads(doc.embedding)
            serialized.append(doc_dict)

        return Response(
            200,
            content=Content(b"application/json", json.dumps(serialized).encode("utf-8"))
        )


def setup_document_routes(app):
    # No se agrega nada manualmente
    pass

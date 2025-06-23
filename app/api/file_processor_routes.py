from blacksheep import get, post, Request, Response
from blacksheep.contents import Content
from starlette.datastructures import UploadFile
from app.services.file_processor import (
    extract_text_from_pdf_bytes,
    extract_text_from_image_bytes
)
import json
from app.services.mcp_document_service import save_mcp_document
from base64 import b64decode
from app.services.embedding_service import generate_embedding
import pickle
from app.db.models import McpDocument
from app.db.database import async_session
from sqlmodel import select
from sqlalchemy import text

@post("/process")
async def process_file(request: Request) -> Response:
    body = await request.json()
    filename = body.get("filename", "archivo.pdf").lower()
    content_base64 = body.get("content_base64")
    path = body.get("path", "root")  # 👈 nuevo

    if not content_base64:
        return Response(
            400,
            content=Content(b"application/json", json.dumps({"error": "Falta el contenido en base64."}).encode("utf-8"))
        )

    try:
        content = b64decode(content_base64)

        if filename.endswith(".pdf"):
            text = extract_text_from_pdf_bytes(content)
        elif filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
            text = extract_text_from_image_bytes(content)
        else:
            return Response(
                415,
                content=Content(b"application/json", json.dumps({"error": "Formato no soportado."}).encode("utf-8"))
            )

        embedding = generate_embedding(text)
        await save_mcp_document(filename, text, embedding, path)  # 👈 pasamos path

        return Response(
            200,
            content=Content(b"application/json", json.dumps({ "text": text }).encode("utf-8"))
        )

    except Exception as e:
        return Response(
            500,
            content=Content(b"application/json", json.dumps({ "error": str(e) }).encode("utf-8"))
        )


@post("/process-base64")
async def process_file_base64(request: Request) -> Response:
    try:
        data = await request.json()
        filename = data.get("filename")
        base64_data = data.get("base64_data")
        path = data.get("path", "root")  # 👈 nuevo

        if not filename or not base64_data:
            return Response(400, content=Content(
                b"application/json",
                json.dumps({"error": "Se requiere 'filename' y 'base64_data'."}).encode("utf-8")
            ))

        raw_bytes = b64decode(base64_data)
        if filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf_bytes(raw_bytes)
        elif filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
            text = extract_text_from_image_bytes(raw_bytes)
        else:
            return Response(415, content=Content(
                b"application/json",
                json.dumps({"error": "Formato no soportado. Solo PDF o imagen."}).encode("utf-8")
            ))

        embedding = generate_embedding(text)
        await save_mcp_document(filename, text, embedding, path) 

        return Response(200, content=Content(
            b"application/json",
            json.dumps({"filename": filename, "text": text[:300]}).encode("utf-8")
        ))

    except Exception as e:
        return Response(500, content=Content(
            b"application/json",
            json.dumps({"error": str(e)}).encode("utf-8")
        ))

    
@get("/mcp/explore-dir")
async def explore_dir():
    async with async_session() as session:
        result = await session.execute(select(McpDocument))
        docs = result.scalars().all()

    return [
        {
            "filename": doc.filename,
            "path": doc.path
        }
        for doc in docs
    ]

@get("/mcp/search-pgvector")
async def search_mcp_pgvector(request: Request) -> Response:
    query = request.query.get("query")
    if not query:
        return Response(400, content=Content(
            b"application/json",
            json.dumps({"error": "Falta el parámetro ?query="}).encode("utf-8")
        ))

    query_embedding = generate_embedding(query)

    sql = text("""
        SELECT id, filename, content, path, created_at,
        embedding_pg <#> :query_vector AS distance
        FROM mcpdocument
        ORDER BY distance ASC
        LIMIT 5
    """)

    async with async_session() as session:
        vector_str = f"[{', '.join(map(str, query_embedding))}]"
        result = await session.execute(sql, {"query_vector": vector_str})
        rows = result.mappings().all()

    payload = [
        {
            "filename": row["filename"],
            "score": round(1 - row["distance"], 4),  # Convertimos distancia a similitud
            "path": row["path"],
            "content_snippet": row["content"][:300],
            "created_at": row["created_at"].isoformat()
        }
        for row in rows
    ]

    return Response(200, content=Content(
        b"application/json",
        json.dumps(payload).encode("utf-8")
    ))

def setup_document_routes(app):
    # No se agrega nada manualmente
    pass
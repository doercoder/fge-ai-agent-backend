from blacksheep import post, Request, Response
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

@post("/process")
async def process_file(request: Request) -> Response:
    body = await request.json()
    filename = body.get("filename", "archivo.pdf").lower()
    content_base64 = body.get("content_base64")

    if not content_base64:
        return Response(
            400,
            content=Content(b"application/json", json.dumps({"error": "Falta el contenido en base64."}).encode("utf-8"))
        )

    try:
        content = base64.b64decode(content_base64)

        if filename.endswith(".pdf"):
            text = extract_text_from_pdf_bytes(content)
        elif filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
            text = extract_text_from_image_bytes(content)
        else:
            return Response(
                415,
                content=Content(b"application/json", json.dumps({"error": "Formato no soportado."}).encode("utf-8"))
            )

        await save_mcp_document(filename, text)
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
        await save_mcp_document(filename, text, embedding)

        return Response(200, content=Content(
            b"application/json",
            json.dumps({"filename": filename, "text": text[:300]}).encode("utf-8")
        ))

    except Exception as e:
        return Response(500, content=Content(
            b"application/json",
            json.dumps({"error": str(e)}).encode("utf-8")
        ))

def setup_document_routes(app):
    # No se agrega nada manualmente
    pass
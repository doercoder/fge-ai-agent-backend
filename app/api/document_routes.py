from blacksheep import post, get, Request, Response
from blacksheep.contents import Content
from app.db.models import Document
from app.db.database import async_session
from sqlmodel import select
from app.services.embedding_service import generate_embedding
import json
import pickle
from base64 import b64decode
from app.services.file_processor import extract_text_from_pdf_bytes, extract_text_from_image_bytes


@post("/documents")
async def create_document(request: Request) -> Response:
    # Endpoint para crear un documento con su contenido
    body = await request.json()
    title = body.get("title", "")
    content = body.get("content", "")

    # Generar embedding para el contenido del documento
    embedding = generate_embedding(content)
    embedding_bytes = pickle.dumps(embedding)

    # Crear el documento en la base de datos
    new_doc = Document(title=title, content=content, embedding=embedding_bytes)

    async with async_session() as session:
        session.add(new_doc)
        await session.commit()
        await session.refresh(new_doc)

        # Devolver el documento creado con sus detalles
        doc_dict = new_doc.model_dump()
        if new_doc.embedding:
            doc_dict["embedding"] = pickle.loads(new_doc.embedding)

        return Response(
            201,
            content=Content(b"application/json", json.dumps(doc_dict).encode("utf-8"))
        )


@post("/process-document")
async def process_document(request: Request) -> Response:
    # Endpoint para procesar un documento recibido en base64 (imagen o PDF)
    body = await request.json()
    base64_data = body.get("base64_data")
    file_type = body.get("file_type", "pdf")  # Tipo de archivo por defecto: PDF

    try:
        # Decodificar el contenido base64
        binary_data = b64decode(base64_data)
        
        # Extraer texto dependiendo del tipo de archivo
        if file_type == "image":
            text = extract_text_from_image_bytes(binary_data)
        else:
            text = extract_text_from_pdf_bytes(binary_data)

    except Exception as e:
        return Response(400, content=Content(b"application/json", json.dumps({"error": str(e)}).encode()))

    # Obtener título y generar embedding para el contenido extraído
    title = body.get("title", "Documento Procesado")
    embedding_vector = await generate_embedding(text)
    embedding = pickle.dumps(embedding_vector)


    # Guardar el documento en la base de datos
    async with async_session() as session:
        doc = Document(title=title, content=text, embedding=embedding)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

    # Retornar detalles del documento procesado
    return Response(200, content=Content(b"application/json", json.dumps({
        "id": doc.id,
        "title": doc.title,
        "preview": text[:500]  # Mostrar un resumen del texto (opcional)
    }).encode()))


@get("/documents")
async def search_documents(request: Request) -> Response:
    # Endpoint para obtener todos los documentos almacenados
    async with async_session() as session:
        result = await session.execute(select(Document))
        documents = result.scalars().all()

        # Serializar los documentos para la respuesta
        serialized = []
        for doc in documents:
            doc_dict = doc.model_dump()
            if doc.embedding:
                doc_dict["embedding"] = pickle.loads(doc.embedding)  # Deserializar embedding
            serialized.append(doc_dict)

        return Response(
            200,
            content=Content(b"application/json", json.dumps(serialized).encode("utf-8"))
        )


def setup_document_routes(app):
    # Aquí se registran las rutas de documentos (en caso de necesitar configuraciones adicionales)
    pass

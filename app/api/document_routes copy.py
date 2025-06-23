from blacksheep import post, get, Request, Response
from blacksheep.contents import Content
from app.services.document_service import insert_document, find_similar_documents
import json

@post("/documents")
async def create_document(request: Request) -> Response:
    data = await request.json()
    title = data.get("title", "Untitled")
    content = data.get("content", "")

    doc = await insert_document(title, content)

    return Response(
        200,
        content=Content(b"application/json", json.dumps({
            "id": doc.id,
            "title": doc.title
        }).encode("utf-8"))
    )

@get("/documents/search")
async def search_documents(request: Request) -> Response:
    query = request.query.get("q")
    if not query:
        return Response(
            400,
            content=Content(
                b"application/json",
                json.dumps({"error": "Missing query parameter 'q'"}).encode("utf-8")
            )
        )

    results = await find_similar_documents(query)
    return Response(
        200,
        content=Content(b"application/json", json.dumps(results).encode("utf-8"))
    )

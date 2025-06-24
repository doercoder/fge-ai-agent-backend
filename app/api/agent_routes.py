from blacksheep import post, get, Request, Response
from blacksheep.contents import Content
from app.agent.agent_core import MomostenangoAgent
from app.api.document_routes import setup_document_routes
from app.api import file_processor_routes 
from app.services.session_service import save_session
from sqlmodel import select
from app.db.models import Session as SessionModel
from app.db.database import async_session
import json
from app.db.models import McpDocument
from app.services.embedding_service import generate_embedding, cosine_similarity
from app.db.models import McpDocument
import pickle
from app.agent.tool_engine import combinar_prompt
from blacksheep.contents import StreamedContent
from sqlalchemy import text
import json
import time
from app.services.metrics_service import log_latency
from app.services.metrics_service import obtener_metricas_latencia

agent = MomostenangoAgent()

def setup_routes(app):
    setup_document_routes(app)

    @post("/chat")
    async def chat(request: Request) -> Response:
        body = await request.json()
        prompt = body.get("prompt", "")
        user_id = body.get("user_id", "anon")
        session_id = body.get("session_id", "0")  # 👈 default sesión 0

        base64_file = body.get("base64_file")  # opcional
        filename = body.get("filename", "")    # opcional

        from app.services.file_processor import extract_text_from_pdf_bytes, extract_text_from_image_bytes
        from base64 import b64decode

        if base64_file and filename:
            try:
                raw_bytes = b64decode(base64_file)
                extracted_text = ""

                if filename.lower().endswith(".pdf"):
                    extracted_text = extract_text_from_pdf_bytes(raw_bytes)
                elif filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
                    extracted_text = extract_text_from_image_bytes(raw_bytes)
                else:
                    print("[CHAT] Tipo de archivo no soportado:", filename)

                if extracted_text:
                    prompt = f"Contenido visual: {extracted_text.strip()}\n\nUsuario dijo: {prompt}"
            except Exception as e:
                print(f"[CHAT] Error al procesar archivo base64: {str(e)}")

        start = time.perf_counter() # para que veamos si sale o no optimizada esta madre, sus tiempos

        reply = await agent.responder(prompt, session_id=session_id)

        await save_session(user_id, session_id, prompt, reply.get("text", ""))

        latency_ms = (time.perf_counter() - start) * 1000
        await log_latency("/chat", latency_ms)

        return Response(
            200,
            content=Content(b"application/json", json.dumps(reply).encode("utf-8"))
        )

    @get("/sessions/{user_id}")
    async def get_user_sessions(user_id: str) -> Response:
        async with async_session() as session:
            result = await session.execute(
                select(SessionModel).where(SessionModel.user_id == user_id)
            )
            sessions = result.scalars().all()
            payload = []
            for s in sessions:
                data = s.model_dump()
                data["created_at"] = data["created_at"].isoformat() if data["created_at"] else None
                payload.append(data)
            return Response(
                200,
                content=Content(b"application/json", json.dumps(payload).encode("utf-8"))
            )

    @get("/sessions/{user_id}/{session_id}")
    async def get_user_session_by_id(user_id: str, session_id: str) -> Response:
        async with async_session() as session:
            result = await session.execute(
                select(SessionModel).where(
                    (SessionModel.user_id == user_id) &
                    (SessionModel.session_id == session_id)
                ).order_by(SessionModel.created_at)
            )
            sessions = result.scalars().all()
            payload = []
            for s in sessions:
                data = s.model_dump()
                data["created_at"] = data["created_at"].isoformat() if data["created_at"] else None
                payload.append(data)
            return Response(
                200,
                content=Content(b"application/json", json.dumps(payload).encode("utf-8"))
            )
        
    @get("/mcp/list-docs")
    async def list_mcp_documents() -> Response:
        async with async_session() as session:
            result = await session.execute(select(McpDocument))
            docs = result.scalars().all()
            payload = [
                { "filename": d.filename, "created_at": d.created_at.isoformat() }
                for d in docs
            ]
            return Response(200, content=Content(b"application/json", json.dumps(payload).encode("utf-8")))

    @get("/mcp/search")
    async def search_mcp_documents(request: Request) -> Response:
        query = request.query.get("query")
        top_k_raw = request.query.get("top_k", ["5"])
        top_k = int(top_k_raw[0]) if isinstance(top_k_raw, list) else int(top_k_raw)


        if not query:
            return Response(
                400,
                content=Content(
                    b"application/json",
                    json.dumps({"error": "Falta el parámetro ?query="}).encode("utf-8")
                )
            )

        query_embedding = generate_embedding(query)
        vector_str = f"[{', '.join(map(str, query_embedding))}]"

        sql = text("""
            SELECT filename, content, path, created_at,
                  embedding_pg <#> :query_vector AS distance
            FROM mcpdocument
            ORDER BY distance ASC
            LIMIT :top_k
        """)

        async with async_session() as session:
            result = await session.execute(sql, {
                "query_vector": vector_str,
                "top_k": top_k
            })
            rows = result.mappings().all()

        payload = [
            {
                "filename": row["filename"],
                "score": round(1 - row["distance"], 4),
                "path": row["path"],
                "content_snippet": row["content"][:300],
                "created_at": row["created_at"].isoformat()
            }
            for row in rows
        ]

        return Response(
            200,
            content=Content(
                b"application/json",
                json.dumps(payload).encode("utf-8")
            )
        )

    @post("/chat-stream")
    async def chat_stream(request: Request) -> Response:
        body = await request.json()
        if body is None:
            return Response(
                400,
                content="data: Error: El cuerpo de la petición está vacío o mal formateado\n\n".encode("utf-8")
            )

        prompt = body.get("prompt", "")
        user_id = body.get("user_id", "anon")
        session_id = body.get("session_id", "0")
        base64_file = body.get("base64_file")
        filename = body.get("filename")

        full_prompt = combinar_prompt(prompt, base64_file, filename)

        async def stream_tokens():
            start = time.perf_counter()
            collected = ""
            async for token in agent.stream_responder(full_prompt, session_id=session_id):
                collected += token
                yield f"data: {token}\n\n".encode("utf-8")

            await save_session(user_id, session_id, full_prompt, collected)
            latency_ms = (time.perf_counter() - start) * 1000
            await log_latency("/chat-stream", latency_ms)
        return Response(
            200,
            content=StreamedContent(b"text/event-stream", stream_tokens)
        )
    
    @get("/metrics/latencia")
    async def get_latency_metrics(request: Request) -> Response:
        endpoint = request.query.get("endpoint", ["/chat"])[0]
        metrics = await obtener_metricas_latencia(endpoint)
        return Response(
            200,
            content=Content(b"application/json", json.dumps(metrics).encode("utf-8"))
        )

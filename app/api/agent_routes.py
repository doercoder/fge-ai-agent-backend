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

agent = MomostenangoAgent()

def setup_routes(app):
    setup_document_routes(app)

    @post("/chat")
    async def chat(request: Request) -> Response:
        body = await request.json()
        prompt = body.get("prompt", "")
        user_id = body.get("user_id", "anon")
        session_id = body.get("session_id", "0")  # 👈 default sesión 0

        reply = await agent.responder(prompt, session_id=session_id)

        await save_session(user_id, session_id, prompt, reply.get("text", ""))

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
        if not query:
            return Response(
                400,
                content=Content(
                    b"application/json",
                    json.dumps({"error": "Falta el parámetro ?query="}).encode("utf-8")
                )
            )


        query_embedding = generate_embedding(query)

        async with async_session() as session:
            result = await session.execute(select(McpDocument))
            docs = result.scalars().all()

            results = []
            for doc in docs:
                if doc.embedding:
                    doc_vector = pickle.loads(doc.embedding)
                    score = cosine_similarity(query_embedding, doc_vector)
                    results.append({
                        "filename": doc.filename,
                        "score": round(score, 4),
                        "content_snippet": doc.content[:300]
                    })

            results.sort(key=lambda r: r["score"], reverse=True)
            return Response(
                200,
                content=Content(b"application/json", json.dumps(results).encode("utf-8"))
            )
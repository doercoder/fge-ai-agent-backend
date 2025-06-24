# app/agent/pothole_report_tool.py
from app.agent.tool_engine import Tool
from app.db.models import PotholeReport, McpDocument
from app.db.database import async_session
from app.services.embedding_service import generate_embedding
from app.agent.llm_singleton import get_llm_agent
from base64 import b64decode
from datetime import datetime
import pickle

class PotholeReportTool(Tool):
    name = "pothole_report"
    keywords = ["bache", "poste", "averiado", "hueco"]

    async def __call__(self, query: str, context: dict = None) -> dict:
        lowered = query.lower()
        if not any(palabra in lowered for palabra in ["bache", "poste", "hueco"]):
            return None  # ❌ No contiene palabras clave, dejar paso a otras tools

        tipo = (
            "bache" if "bache" in lowered else
            "poste" if "poste" in lowered else
            "reporte"
        )

        # 🧠 Extraer ubicación con modelo
        agent = get_llm_agent()
        prompt_llm = f"""
Eres un sistema municipal que extrae ubicaciones geográficas de mensajes ciudadanos. 
Extrae la dirección o referencia de ubicación del siguiente mensaje. Si no hay ubicación clara, responde "desconocida".

Mensaje: {query}

Ubicación:
""".strip()
        response = await agent.arun(prompt_llm)
        ubicacion = response.content.strip()
        if not ubicacion or "desconocida" in ubicacion.lower():
            ubicacion = "ubicación no especificada"

        filename = context.get("filename") if context else None
        base64_file = context.get("base64_file") if context else None

        async with async_session() as session:
            # Guardar en la tabla de reportes
            nuevo = PotholeReport(
                tipo=tipo,
                ubicacion=ubicacion,
                prompt_original=query,
                filename=filename,
                etiquetas=None
            )
            session.add(nuevo)

            # Solo guardar en MCP si hay archivo
            if base64_file:
                try:
                    raw_bytes = b64decode(base64_file)
                    from app.services.file_processor import extract_text_from_image_bytes
                    extracted = extract_text_from_image_bytes(raw_bytes)
                    content = f"{query}\n\n{extracted}"

                    embedding = generate_embedding(content)
                    mcp = McpDocument(
                        filename=filename or f"reporte_{tipo}_{nuevo.created_at.isoformat()}",
                        content=content,
                        embedding=pickle.dumps(embedding),
                        embedding_pg=embedding,
                        path="reportes"
                    )
                    session.add(mcp)

                except Exception as e:
                    print(f"[TOOL:pothole] Error OCR imagen: {e}")

            await session.commit()

            return {
                "respuesta": f"✅ Tu reporte fue registrado con número **#{nuevo.id}**, ubicado en: **{ubicacion}**.",
                "topic": "reporte_municipal"
            }

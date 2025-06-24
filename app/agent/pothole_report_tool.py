from app.agent.tool_engine import Tool
from app.db.models import PotholeReport, McpDocument
from app.db.database import async_session
from app.services.embedding_service import generate_embedding
from app.agent.llm_singleton import get_llm_agent
from base64 import b64decode
from datetime import datetime
import pickle
import re

class PotholeReportTool(Tool):
    name = "pothole_report"
    keywords = ["bache", "poste", "hueco"]  # Palabras clave para activar la tool

    def should_trigger(self, text: str) -> bool:
        """Asegura que se activa solo cuando se menciona una acción de reporte explícita"""
        text = text.lower()
        # Comprobamos que haya una acción + mención válida (bache/poste/hueco)
        if any(verb in text for verb in ["reportar", "avisar", "encontré", "ver", "informar"]):
            return any(kw in text for kw in self.keywords)
        return False

    async def __call__(self, query: str, context: dict = None) -> dict:
        lowered = query.lower()

        # Solo procesar si la tool fue activada por una acción y términos clave
        if not self.should_trigger(query):
            return None  # ❌ No contiene las condiciones para activarse, dejar paso a otras tools

        # Determinar tipo de incidente
        tipo = (
            "bache" if "bache" in lowered else
            "poste" if "poste" in lowered else
            "hueco"  # Si no está bache o poste, se marca como "hueco" por defecto
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
            ubicacion = "ubicación no especificada"  # Respuesta por defecto si no se encuentra ubicación

        filename = context.get("filename") if context else None
        base64_file = context.get("base64_file") if context else None

        # Guardar el reporte en la base de datos
        async with async_session() as session:
            nuevo = PotholeReport(
                tipo=tipo,
                ubicacion=ubicacion,
                prompt_original=query,
                filename=filename,
                etiquetas=None  # Puedes agregar etiquetas si lo deseas
            )
            session.add(nuevo)

            # Solo guardar en MCP si hay archivo (base64)
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

            # Commit a la base de datos
            await session.commit()

            # Respuesta estructurada para el usuario
            return {
                "respuesta": f"✅ Tu reporte fue registrado con número **#{nuevo.id}**, ubicado en: **{ubicacion}**.",
                "topic": "reporte_municipal"
            }

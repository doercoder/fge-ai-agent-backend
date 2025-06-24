import os
from typing import AsyncGenerator
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from app.agent.tool_engine import ToolEngine
from app.services.municipal_info_tool import MunicipalInfoTool
from app.agent.structured_output import build_structured_output
from app.db.database import async_session
from app.db.models import McpDocument
from app.services.embedding_service import generate_embedding
from sqlalchemy import text
import re


class MomostenangoAgent:
    def __init__(self):
        self.tools = [MunicipalInfoTool()]
        self.tool_engine = ToolEngine(self.tools)
        self.agent = Agent(
            model=OpenRouter(
                id="mistralai/mistral-7b-instruct:free",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        )
    @staticmethod
    def extraer_top_k(prompt: str, default: int = 4) -> int:
        matches = re.findall(r"top[\s-]?(\d{1,2})", prompt.lower())
        if matches:
            k = int(matches[0])
            return min(max(k, 1), 20)  # limita de 1 a 20 para seguridad
        return default

    def should_trigger_mcp_search(self, prompt: str) -> bool:
        triggers = ["mcp", "repositorio", "documento", "ley", "reglamento"]
        return any(trigger in prompt.lower() for trigger in triggers)

    async def buscar_en_mcp(self, query: str, top_k: int = 4) -> str:
        query_embedding = generate_embedding(query)
        vector_str = f"[{', '.join(map(str, query_embedding))}]"

        sql = text("""
            SELECT filename, content, embedding_pg <#> :query_vector AS distance
            FROM mcpdocument
            ORDER BY distance ASC
            LIMIT :top_k
        """)

        async with async_session() as session:
            result = await session.execute(sql, {"query_vector": vector_str, "top_k": top_k})
            rows = result.mappings().all()

        context_parts = []
        for row in rows:
            snippet = row["content"][:800].strip().replace("\n", " ")
            context_parts.append(f"[{row['filename']}]: {snippet}...")

        return "\n\n".join(context_parts)

    async def responder(self, prompt: str, session_id: str = "default") -> dict:
        print(f"[AGENTE] Prompt recibido: {prompt}")
        used_tools = set()

        # Paso 1: Ejecutar tools antes del LLM
        result = await self.tool_engine.run_tools_before_llm(prompt, used_tools)
        if result:
            return build_structured_output(
                text=result["text"],
                intent="tool_response",
                source=result["used"][0],
                session_id=session_id,
                extra={"topic": result["topic"], "confidence": 0.95, "tools_called": result["used"]}
            )

        # Paso 1.5: Si el prompt parece una consulta al MCP
        if self.should_trigger_mcp_search(prompt):
            print("[AGENTE] Activando búsqueda en MCP...")
            top_k = MomostenangoAgent.extraer_top_k(prompt)
            context = await self.buscar_en_mcp(prompt, top_k=top_k)
            contextual_prompt = f"""El usuario preguntó: "{prompt}"

Aquí hay contexto recuperado desde el repositorio MCP:

{context}

Con base en este contexto, responde de forma clara y útil.
"""
            response = await self.agent.arun(contextual_prompt)
            full_text = response.content
            print(f"[AGENTE] LLM respondió con contexto MCP: {full_text}")
            return build_structured_output(
                text=full_text,
                intent="consulta_mcp",
                source="mcp + openrouter",
                session_id=session_id,
                extra={"context_used": True, "confidence": 0.85}
            )

        # Paso 2: LLM responde sin contexto MCP
        print("[AGENTE] Usando LLM (OpenRouter).")
        response = await self.agent.arun(prompt)
        full_text = response.content
        print(f"[AGENTE] LLM respondió: {full_text}")

        # Paso 3: Tools después del LLM
        extras = await self.tool_engine.run_tools_after_llm(full_text, used_tools)

        if extras:
            appended_text = "\n\nAdemás, encontré información útil:\n" + "\n".join(
                [e["text"] for e in extras]
            )
            full_text += appended_text
            sources = ["openrouter"] + [e["tool"] for e in extras]
        else:
            sources = ["openrouter"]

        return build_structured_output(
            text=full_text,
            intent="respuesta_general" if not extras else "respuesta_compuesta",
            source=" + ".join(sources),
            session_id=session_id,
            extra={
                "confidence": 0.75 if not extras else 0.9,
                "tools_called": list(used_tools)
            }
        )

    async def stream_responder(self, prompt: str, session_id: str = "default") -> AsyncGenerator[str, None]:
        used_tools = set()

        # Paso 1: Ejecutar tools antes del LLM
        result = await self.tool_engine.run_tools_before_llm(prompt, used_tools)
        if result:
            for token in result["text"]:
                yield token
            return

        # Paso 1.5: Si es consulta al MCP, buscar contexto
        if self.should_trigger_mcp_search(prompt):
            print("[AGENTE] Streaming con contexto MCP...")
            top_k = MomostenangoAgent.extraer_top_k(prompt)
            context = await self.buscar_en_mcp(prompt, top_k=top_k)
            contextual_prompt = f"""El usuario preguntó: "{prompt}"

Aquí hay contexto recuperado desde el repositorio MCP:

{context}

Con base en este contexto, responde de forma clara y útil.
"""
            run_response = await self.agent.arun(contextual_prompt, stream=True)
        else:
            run_response = await self.agent.arun(prompt, stream=True)

        # Paso 2: Emitir tokens del stream
        async for chunk in run_response:
            if chunk.content:
                yield chunk.content





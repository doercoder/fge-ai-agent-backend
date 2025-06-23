# app/agent/agent_core.py
import os
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from app.services.municipal_info_tool import MunicipalInfoTool  # 👈 importar tool

class MomostenangoAgent:
    def __init__(self):
        self.tools = [MunicipalInfoTool()]
        self.agent = Agent(
            model=OpenRouter(
                id="mistralai/mistral-7b-instruct:free",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        )

    async def responder(self, prompt: str, session_id: str = "default") -> dict:
        print(f"[AGENTE] Prompt recibido: {prompt}")
        print(f"[AGENTE] Session ID: {session_id}")

        for tool in self.tools:
            print(f"[AGENTE] Probando tool: {tool.name}")
            result = await tool(prompt)
            if result:
                print(f"[AGENTE] Tool {tool.name} respondió: {result['respuesta']}")
                return {
                    "text": result["respuesta"],
                    "data": {
                        "intent": "tool_response",
                        "session_id": session_id,
                        "source": tool.name
                    }
                }

        # Tool no respondió: usar LLM con introducción
        print("[AGENTE] Ninguna tool respondió. Usando LLM (OpenRouter).")
        response = await self.agent.arun(prompt)
        print(f"[AGENTE] LLM respondió: {response.content}")

        prefacio = (
            "La consulta está fuera de nuestras herramientas municipales, "
            "por lo que investigando en internet te puedo responder que:\n\n"
        )

        return {
            "text": prefacio + response.content,
            "data": {
                "intent": "respuesta_general",
                "session_id": session_id,
                "source": "openrouter"
            }
        }

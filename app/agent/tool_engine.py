from typing import List, Dict, Set
import base64
from app.services.file_processor import extract_text_from_pdf_bytes, extract_text_from_image_bytes
import re
from app.agent.structured_output import build_structured_output


class Tool:
    name: str = "unnamed_tool"
    keywords: List[str] = []  # palabras clave que activan la tool en postprocesamiento

    async def __call__(self, query: str, context: dict = None) -> Dict:
        raise NotImplementedError("Tool debe implementar __call__")

    def should_trigger(self, text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in self.keywords)


class ToolEngine:
    def __init__(self, tools: List[Tool]):
        self.tools = tools

    async def run_tools_before_llm(self, prompt: str, used_tools: Set[str], context: dict = None) -> Dict:
        for tool in self.tools:
            if tool.name not in used_tools:
                print(f"[TOOL_ENGINE] Probando tool: {tool.name} con prompt: {prompt}")
                result = await tool(prompt, context=context)
                if result:
                    used_tools.add(tool.name)
                    print(f"[TOOL_ENGINE] Tool activada: {tool.name}")
                    
                    return build_structured_output(
                        text=result.get("respuesta", result.get("text", "")),
                        intent="tool_response",
                        source=tool.name,
                        session_id=context.get("session_id", "default") if context else "default",
                        structured=result.get("structured"),
                        extra={
                            "topic": result.get("topic", "desconocido"),
                            "confidence": 0.95,
                            "tools_called": [tool.name]
                        }
                    )
        return {}



    async def run_tools_after_llm(self, response_text: str, used_tools: Set[str]) -> List[Dict]:
        extra_responses = []
        for tool in self.tools:
            if tool.name not in used_tools and tool.should_trigger(response_text):
                result = await tool(response_text)
                if result:
                    used_tools.add(tool.name)
                    extra_responses.append({
                        "text": result["respuesta"],
                        "tool": tool.name,
                        "topic": result.get("topic", "desconocido")
                    })
        return extra_responses


class TrashScheduleTool(Tool):
    name = "trash_schedule"
    keywords = ["basura", "recolección", "zona"]

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = text.replace("\n", " ")
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    async def __call__(self, query: str, context: dict = None) -> Dict:
        cleaned = self.normalize_text(query)
        print(f"[TOOL:trash_schedule] Texto limpiado: '{cleaned}'")

        zonas = {
            "zona 1": "La recolección de basura en zona 1 es lunes y jueves a las 6:00 AM.",
            "zona 2": "En zona 2 pasan martes y viernes a las 9:00 AM.",
            "zona 3": "En zona 3 pasan miércoles y sábado a las 7:00 AM.",
            "zona 4": "La recolección en zona 4 es martes y viernes a las 6:30 AM.",
            "zona 5": "En zona 5 pasan lunes y jueves a las 8:00 AM.",
            "zona 6": "La basura en zona 6 se recoge miércoles y sábado a las 9:30 AM.",
            "zona 7": "En zona 7 pasan los lunes, miércoles y viernes a las 7:00 AM.",
            "zona 8": "Zona 8 tiene recolección martes y sábado a las 6:00 AM.",
            "zona 9": "Los camiones pasan por zona 9 los jueves y domingos a las 8:15 AM.",
            "zona 10": "En zona 10, la recolección es lunes, miércoles y sábado a las 7:30 AM.",
        }


        for zona, respuesta in zonas.items():
            if zona in cleaned:
                print(f"🟢 Tool activada para {zona}")
                return {"respuesta": respuesta, "topic": "basura"}

        return None



class FormAccessTool(Tool):
    name = "form_access"
    keywords = ["formulario", "permiso", "trámite"]

    async def __call__(self, query: str, context: dict = None) -> Dict:
        if "permiso de construcción" in query.lower():
            return {"respuesta": "Puedes descargar el formulario de permiso de construcción aquí: https://municipalidad.gob.gt/formularios/construccion.pdf", "topic": "formularios"}
        elif "trámite" in query.lower():
            return {"respuesta": "Los formularios están disponibles en https://municipalidad.gob.gt/formularios", "topic": "formularios"}
        return None



def combinar_prompt(prompt: str, base64_file: str = None, filename: str = None) -> str:
    if base64_file and filename:
        try:
            raw_bytes = base64.b64decode(base64_file)
            extracted_text = ""
            if filename.lower().endswith(".pdf"):
                extracted_text = extract_text_from_pdf_bytes(raw_bytes)
            elif filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
                extracted_text = extract_text_from_image_bytes(raw_bytes)
            if extracted_text:
                return f"Contenido visual: {extracted_text.strip()}\n\nUsuario dijo: {prompt}"
        except Exception as e:
            print(f"[TOOL_ENGINE] Error al procesar archivo base64: {e}")
    return prompt

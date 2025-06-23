from typing import List, Dict, Set
import base64
from app.services.file_processor import extract_text_from_pdf_bytes, extract_text_from_image_bytes

class Tool:
    name: str = "unnamed_tool"
    keywords: List[str] = []  # palabras clave que activan la tool en postprocesamiento

    async def __call__(self, query: str) -> Dict:
        raise NotImplementedError("Tool debe implementar __call__")

    def should_trigger(self, text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in self.keywords)


class ToolEngine:
    def __init__(self, tools: List[Tool]):
        self.tools = tools

    async def run_tools_before_llm(self, prompt: str, used_tools: Set[str]) -> Dict:
        for tool in self.tools:
            if tool.name not in used_tools:
                result = await tool(prompt)
                if result:
                    used_tools.add(tool.name)
                    return {
                        "text": result["respuesta"],
                        "used": [tool.name],
                        "topic": result.get("topic", "desconocido")
                    }
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


# Tool 1: TrashScheduleTool
class TrashScheduleTool(Tool):
    name = "trash_schedule"
    keywords = ["basura", "recolección", "zona"]

    async def __call__(self, query: str) -> Dict:
        if "zona 1" in query.lower():
            return {"respuesta": "La recolección de basura en zona 1 es lunes y jueves a las 6:00 AM.", "topic": "basura"}
        elif "zona 3" in query.lower():
            return {"respuesta": "En zona 3 pasan martes y viernes a las 7:00 AM.", "topic": "basura"}
        return None


# Tool 2: FormAccessTool
class FormAccessTool(Tool):
    name = "form_access"
    keywords = ["formulario", "permiso", "trámite"]

    async def __call__(self, query: str) -> Dict:
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

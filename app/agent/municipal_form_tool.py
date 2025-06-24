from app.agent.tool_engine import Tool
from pathlib import Path

class MunicipalFormTool(Tool):
    name = "municipal_form"
    keywords = ["formulario", "solicitud", "permiso", "poda", "evento", "construcción"]

    async def __call__(self, query: str, context: dict = None) -> dict:
        lowered = query.lower()

        if not any(keyword in lowered for keyword in self.keywords):
            return None

        forms = {
            "construcción": "formulario_permiso_construccion.pdf",
            "poda": "solicitud_poda_arbol.pdf",
            "evento": "solicitud_evento_publico.pdf"
        }

        for keyword, filename in forms.items():
            if keyword in lowered:
                return {
                    "respuesta": f"Aquí tienes el formulario de {keyword}.",
                    "structured": {
                        "tipo": "formulario",
                        "nombre": f"Formulario de {keyword}",
                        "archivo": filename,
                        "ubicacion": f"data/forms/{filename}"
                    }
                }

        return {
            "respuesta": "Detecté que necesitas un formulario, pero no encontré uno específico para tu solicitud. ¿Puedes intentar con otra palabra?",
            "structured": None
        }

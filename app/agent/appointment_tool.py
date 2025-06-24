from app.agent.tool_engine import Tool
from typing import Dict
import re

class AppointmentTool(Tool):
    name = "appointment_tool"
    keywords = ["cita", "agendar", "identidad", "salud", "transporte"]

    async def __call__(self, query: str, context: dict = None) -> Dict:
        text = query.lower()

        # Activación: debe tener al menos una keyword
        if not any(k in text for k in self.keywords):
            return None

        tipo = None
        for word in ["identidad", "salud", "transporte"]:
            if word in text:
                tipo = word
                break

        fecha_match = re.search(r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo|\d{4}-\d{2}-\d{2})", text)
        hora_match = re.search(r"(\d{1,2}(:\d{2})?\s?(am|pm)?)", text)

        fecha = fecha_match.group(0) if fecha_match else None
        hora = hora_match.group(0) if hora_match else None

        # Verificar qué falta
        missing = []
        if not tipo:
            missing.append("tipo de servicio (identidad, salud, transporte)")
        if not fecha:
            missing.append("fecha")
        if not hora:
            missing.append("hora")

        if missing:
            return {
                "respuesta": f"Para agendar una cita, necesito: {', '.join(missing)}.",
                "topic": "agenda_cita",
                "structured": {
                    "estado": "incompleto",
                    "faltantes": missing
                }
            }

        return {
            "respuesta": f"Cita agendada para {tipo} el {fecha} a las {hora}. ¡Gracias por usar el asistente municipal!",
            "topic": "agenda_cita",
            "structured": {
                "estado": "confirmado",
                "tipo": tipo,
                "fecha": fecha,
                "hora": hora
            }
        }

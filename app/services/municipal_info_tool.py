from typing import Dict

class MunicipalInfoTool:
    name = "municipal_info"
    description = "Devuelve información sobre servicios municipales como recolección de basura o trámites."

    async def __call__(self, query: str) -> Dict:
        query = query.lower()
        if "basura" in query and "zona 1" in query:
            return {"respuesta": "La recolección de basura en zona 1 es lunes y jueves a las 6:00 AM."}
        if "bache" in query:
            return {"respuesta": "Puede reportar un bache llamando al 1520 o desde la app municipal."}
        if "formulario" in query:
            return {"respuesta": "Los formularios para trámites están en https://municipalidad.gob.gt/formularios"}
        return None

from app.db.database import async_session
from app.db.models import LatencyLog
from statistics import median, quantiles
from typing import Literal
from datetime import timedelta, datetime
from sqlalchemy import text

async def log_latency(endpoint: str, duration_ms: float):
    async with async_session() as session:
        entry = LatencyLog(endpoint=endpoint, duration_ms=duration_ms)
        session.add(entry)
        await session.commit()


async def obtener_metricas_latencia(endpoint: Literal["/chat", "/chat-stream"], ultimos_minutos: int = 60):
    async with async_session() as session:
        desde = datetime.utcnow() - timedelta(minutes=ultimos_minutos)
        result = await session.execute(
            text("""
                SELECT duration_ms
                FROM latencylog
                WHERE endpoint = :endpoint
                  AND timestamp >= :desde
                ORDER BY timestamp DESC
                LIMIT 100
            """),
            {"endpoint": endpoint, "desde": desde}
        )
        duraciones = [r[0] for r in result.fetchall()]

    if not duraciones:
        return {"p50": None, "p90": None, "p95": None, "count": 0}

    p50 = median(duraciones)
    p90 = quantiles(duraciones, n=100)[89]
    p95 = quantiles(duraciones, n=100)[94]

    return {
        "p50": round(p50, 2),
        "p90": round(p90, 2),
        "p95": round(p95, 2),
        "count": len(duraciones)
    }

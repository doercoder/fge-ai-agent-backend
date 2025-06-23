import os
import httpx

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistral/mistral-7b-instruct:free"

async def llamar_modelo(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "fge-ai-agent-backend",
        "HTTP-Referer": "http://localhost:8000"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


import openai
import os
import numpy as np
from typing import List
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

USE_FAKE_EMBEDDING = False  # Cambiá a True para simular sin usar tokens reales

def generate_fake_embedding(text: str, dim: int = 384) -> List[float]:
    import hashlib
    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (10 ** 8)
    rng = np.random.default_rng(seed)
    return rng.random(dim).tolist()

def generate_real_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def generate_embedding(text: str) -> List[float]:
    if USE_FAKE_EMBEDDING:
        return generate_fake_embedding(text)
    return generate_real_embedding(text)

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    a = np.array(vec1)
    b = np.array(vec2)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return float(dot / (norm_a * norm_b))

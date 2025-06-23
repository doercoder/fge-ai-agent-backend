import numpy as np
from app.db.models import Document
from app.services.embedding_service import generate_embedding, cosine_similarity
from typing import List

async def insert_document(title: str, content: str):
    vector = generate_embedding(content)
    # PostgreSQL espera vector como bytes
    vector_bytes = np.array(vector, dtype=np.float32).tobytes()
    return await Document.objects.create(title=title, content=content, embedding=vector_bytes)

async def find_similar_documents(query: str, top_k: int = 3) -> List[dict]:
    query_embedding = generate_embedding(query)
    documents = await Document.objects.all()
    scored_docs = []
    for doc in documents:
        doc_vector = np.frombuffer(doc.embedding, dtype=np.float32)
        similarity = cosine_similarity(query_embedding, doc_vector.tolist())
        scored_docs.append({"id": doc.id, "title": doc.title, "similarity": similarity})

    return sorted(scored_docs, key=lambda x: x["similarity"], reverse=True)[:top_k]

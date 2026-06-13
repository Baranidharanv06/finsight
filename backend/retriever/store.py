from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid

COLLECTION_NAME = "finsight_chunks"
VECTOR_SIZE = 384  # matches all-MiniLM-L6-v2

client = QdrantClient(path="./qdrant_data")  # local on-disk storage

def init_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

def upsert_chunks(chunks: list[str], vectors: list[list[float]], metadata: dict):
    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": chunk, **metadata}
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def search(query_vector: list[float], top_k: int = 5):
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )
    return results.points
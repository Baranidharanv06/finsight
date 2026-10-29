from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
import uuid

COLLECTION_NAME = "finsight_chunks"
VECTOR_SIZE = 384

client = QdrantClient(path="./qdrant_data")


def init_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )


def delete_ticker(ticker: str):
    """Remove existing chunks for a ticker before re-ingesting."""
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="ticker", match=MatchValue(value=ticker))]
        )
    )


def upsert_chunks(
    chunks: list[str],
    vectors: list[list[float]],
    metadata: dict,
    per_chunk_metadata: list[dict] | None = None,  # ACRE: e.g. [{"sensitivity": 2}, ...]
):
    """
    metadata: shared across every chunk in this batch (e.g. ticker, doc_type) — unchanged.
    per_chunk_metadata: optional, one dict per chunk, merged on top of `metadata`
    for that specific chunk. Used by ACRE to store a per-chunk sensitivity tag.
    If omitted, behaves exactly as before.
    """
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        payload = {"text": chunk, **metadata}
        if per_chunk_metadata is not None:
            payload.update(per_chunk_metadata[i])
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload,
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(query_vector: list[float], top_k: int = 5, ticker: str = None):
    query_filter = None
    if ticker:
        query_filter = Filter(
            must=[FieldCondition(key="ticker", match=MatchValue(value=ticker))]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=query_filter
    )
    return results.points
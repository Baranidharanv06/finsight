from backend.fetcher.sec import get_cik, get_latest_10k_text
from backend.chunker.chunk import chunk_text

cik = get_cik("AAPL")
text = get_latest_10k_text(cik)

chunks = chunk_text(text)
print(f"Total chunks: {len(chunks)}")
print(f"First chunk ({len(chunks[0])} chars):\n")
print(chunks[0])
print(f"Total text length: {len(text)} chars")
from backend.embedder.embed import embed_texts

# Embed just the first 3 chunks for testing
sample_chunks = chunks[:3]
vectors = embed_texts(sample_chunks)

print(f"Embedded {len(vectors)} chunks")
print(f"Vector dimension: {len(vectors[0])}")
print(f"First few values: {vectors[0][:5]}")

from backend.retriever.store import init_collection, upsert_chunks, search

init_collection()

# Embed all chunks (not just 3 this time)
all_vectors = embed_texts(chunks)
print(f"Embedded {len(all_vectors)} chunks total")

upsert_chunks(chunks, all_vectors, metadata={"ticker": "AAPL", "doc_type": "10-K", "year": 2025})
print("Stored in Qdrant")

# Test search
query = "What are the main risk factors?"
query_vector = embed_texts([query])[0]
results = search(query_vector, top_k=3)

for r in results:
    print(f"\nScore: {r.score:.3f}")
    print(r.payload["text"][:200])
    from backend.retriever.store import client as qdrant_client
qdrant_client.close()
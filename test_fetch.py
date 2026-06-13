from backend.fetcher.sec import get_cik, get_latest_10k_text
from backend.chunker.chunk import chunk_text

cik = get_cik("AAPL")
text = get_latest_10k_text(cik)

chunks = chunk_text(text)
print(f"Total chunks: {len(chunks)}")
print(f"First chunk ({len(chunks[0])} chars):\n")
print(chunks[0])
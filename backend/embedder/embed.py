from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text chunks using a local sentence-transformers model.
    Returns a list of vectors (one per input text).
    """
    embeddings = _model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
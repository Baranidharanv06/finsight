import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Split text into overlapping chunks, breaking on paragraph boundaries
    where possible. chunk_size and overlap are in characters (rough proxy
    for tokens at this stage).
    """
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            # start new chunk, carry over overlap from end of previous
            overlap_text = current[-overlap:] if current else ""
            current = (overlap_text + "\n\n" + para) if overlap_text else para

    if current:
        chunks.append(current)

    return chunks
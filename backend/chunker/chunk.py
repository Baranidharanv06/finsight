import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # Break up oversized paragraphs into smaller pieces
    pieces = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            pieces.append(para)
        else:
            for i in range(0, len(para), chunk_size - overlap):
                pieces.append(para[i:i + chunk_size])

    chunks = []
    current = ""

    for piece in pieces:
        if len(current) + len(piece) <= chunk_size:
            current += ("\n\n" if current else "") + piece
        else:
            if current:
                chunks.append(current)
            overlap_text = current[-overlap:] if current else ""
            current = (overlap_text + "\n\n" + piece) if overlap_text else piece

    if current:
        chunks.append(current)

    return chunks
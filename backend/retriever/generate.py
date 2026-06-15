import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are FinSight, a financial document analysis assistant.
Answer the user's question using ONLY the provided context from the company's filings.
If the context doesn't contain enough information to answer, say so clearly.
Always be precise with numbers and figures. Cite which part of the context you used."""

COMPARISON_SYSTEM_PROMPT = """You are FinSight, a financial document analysis assistant.
You will be given a question and context from multiple companies' SEC filings.
Compare how each company addresses the question, using ONLY the provided context.
Structure your answer with a clear section per company, then a brief synthesis of
key similarities and differences. Be precise and cite which filing each point comes from."""


def generate_answer(query: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    user_prompt = f"""Context from financial documents:
{context}

Question: {query}

Answer based only on the context above."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def generate_comparison(query: str, per_company_chunks: dict[str, list[str]]) -> str:
    context_sections = []
    for ticker, chunks in per_company_chunks.items():
        if chunks:
            joined = "\n\n".join(chunks)
            context_sections.append(f"=== {ticker} 10-K excerpts ===\n{joined}")
        else:
            context_sections.append(f"=== {ticker} 10-K excerpts ===\n(No relevant content found)")

    context = "\n\n".join(context_sections)

    user_prompt = f"""{context}

Question: {query}

Compare how each company addresses this, based only on the excerpts above."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
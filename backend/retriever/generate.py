import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are FinSight, a financial document analysis assistant.
Answer the user's question using ONLY the provided context from the company's filings.
If the context doesn't contain enough information to answer, say so clearly.
Always be precise with numbers and figures. Cite which part of the context you used."""

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
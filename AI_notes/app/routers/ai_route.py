from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os

from ..schemas.schemas import QuestionRequest
from ..oauth2 import get_current_user

# --------------------------------------------------
# ENV SETUP
# --------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY")

# --------------------------------------------------
# CLIENTS
# --------------------------------------------------

openai_client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "notes-api"
index = pc.Index(INDEX_NAME)

# --------------------------------------------------
# ROUTER
# --------------------------------------------------

router = APIRouter(prefix="/AI", tags=["AI"])

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def embed_text(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# --------------------------------------------------
# ASK AI
# --------------------------------------------------

@router.post("/ask")
async def ask_ai(
    payload: QuestionRequest,
    current_user=Depends(get_current_user)
):
    # 1️⃣ Embed the question
    question_embedding = embed_text(payload.question)

    # 2️⃣ Query Pinecone (user-scoped)
    query_response = index.query(
        vector=question_embedding,
        top_k=5,
        include_metadata=True,
        filter={
            "user_id": current_user.id
        }
    )

    if not query_response.matches:
        raise HTTPException(
            status_code=404,
            detail="No relevant notes found"
        )

    # 3️⃣ Build context from metadata.text
    context = "\n\n".join(
        match.metadata["text"]
        for match in query_response.matches
        if "text" in match.metadata
    )

    if not context.strip():
        raise HTTPException(
            status_code=500,
            detail="Vector data exists but text metadata is missing"
        )

    # 4️⃣ Ask GPT using retrieved notes
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer ONLY using the provided notes. "
                    "If the answer is not present, say you don't know."
                )
            },
            {
                "role": "user",
                "content": f"NOTES:\n{context}\n\nQUESTION: {payload.question}"
            }
        ]
    )

    return {
        "question": payload.question,
        "answer": completion.choices[0].message.content
    }

from fastapi import APIRouter, Depends, HTTPException
import os
from app.models.ask_model import AskRequest
from app.core.embedder import Embedder
from app.core.vectordb import VectorDB
from app.core.retriever import Retriever
from app.core.generator import Generator
from app.core.ragcore import RAGCore
from app.core.chat_core import chat_core
from app.services.auth_core import auth_service
from app.core.chat_message_core import chat_message_core

router = APIRouter()

embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

retriever = Retriever(vectordb)
generator = Generator()

rag = RAGCore(retriever, generator, chat_message_core)

@router.post("/ask")
def ask_question(
    data: AskRequest,
    user=Depends(auth_service.get_current_user)
):
    chat = chat_core.get_chat(
        chat_id=data.chat_id,
        user_id=user.id
    )

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    result = rag.run(
        query=data.query,
        user_id=user.id,
        chat_id=data.chat_id,
        mode=chat.get("mode", "normal"),
        relevant_doc_ids=data.relevant_doc_ids,
        baseline_latency_sec=data.baseline_latency_sec,
        baseline_hallucination_rate=data.baseline_hallucination_rate,
        user_satisfaction_score=data.user_satisfaction_score
    )

    return result
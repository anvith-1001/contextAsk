from fastapi import APIRouter, UploadFile, File, Depends, Form
import shutil
import os
from app.core.parser import Parser
from app.core.chunker import Chunker
from app.core.indexer import Indexer
from app.core.embedder import Embedder
from app.core.vectordb import VectorDB
from app.services.auth_core import auth_service
from app.core.chat_core import chat_core

router = APIRouter()

embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

chunker = Chunker()
indexer = Indexer(chunker, vectordb)
parser = Parser()

@router.post("/index")
async def index_document(
    chat_id: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(auth_service.get_current_user)
):

    os.makedirs("temp", exist_ok=True)

    file_path = f"temp/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    parsed_text = parser.parse(file_path)

    indexer.index_document(
        text=parsed_text,
        source=file.filename,
        user_id=user.id,
        chat_id=chat_id
    )

    chat_core.update_chat_mode(
        chat_id=chat_id,
        user_id=user.id,
        mode="rag"
    )

    os.remove(file_path)

    return {
        "message": "Document indexed successfully",
        "source": file.filename,
        "chat_id": chat_id,
        "user_id": user.id,
        "mode": "rag"
    }
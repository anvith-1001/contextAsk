import os
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.core.vectordb import VectorDB
from app.core.embedder import Embedder
from app.models.chat_model import CreateChatRequest, UpdateChatNameRequest
from app.core.chat_core import chat_core
from app.services.auth_core import auth_service
from app.core.imggen_core import ImageGenCore
from app.core.chat_message_core import chat_message_core

router = APIRouter()

imggen_core = ImageGenCore(chat_message_core)

embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

@router.post("/create")
def create_chat(
    data: CreateChatRequest,
    user=Depends(auth_service.get_current_user)
):

    chat = chat_core.create_chat(
        user_id=user.id,
        name=data.name,
        mode=data.mode
    )

    return chat

@router.get("/my-chats")
def list_my_chats(
    user=Depends(auth_service.get_current_user)
):

    return chat_core.list_user_chats(user.id)


@router.get("/chat/{chat_id}/messages")
def get_chat_messages(
    chat_id: str,
    user=Depends(auth_service.get_current_user)
):
    try:
        ObjectId(chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid chat_id")

    messages = chat_message_core.get_messages(
        chat_id=chat_id,
        user_id=user.id
    )

    return {
        "chat_id": chat_id,
        "messages": messages
    }

@router.put("/update/{chat_id}")
def update_chat_name(
    chat_id: str,
    data: UpdateChatNameRequest,
    user=Depends(auth_service.get_current_user)
):

    updated_chat = chat_core.update_chat_name(
        chat_id=chat_id,
        user_id=user.id,
        name=data.name
    )

    if not updated_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return updated_chat

# used for initial testing.
"""
@router.get("/{chat_id}")
def get_chat(
    chat_id: str,
    user=Depends(auth_service.get_current_user)
):

    chat = chat_core.get_chat(
        chat_id=chat_id,
        user_id=user.id
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    return chat
"""

@router.delete("/{chat_id}")
def delete_chat(
    chat_id: str,
    user=Depends(auth_service.get_current_user)
):

    deleted = chat_core.delete_chat(
        chat_id=chat_id,
        user_id=user.id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    chat_message_core.collection.delete_many({
        "chat_id": chat_id,
        "user_id": user.id
    })

    imggen_core.collection.delete_many({
        "chat_id": chat_id,
        "user_id": user.id
    })

    vectordb.delete_chat_documents(
        user_id=user.id,
        chat_id=chat_id
    )

    return {
        "message": "Chat deleted"
    }
from fastapi import APIRouter, Depends, HTTPException
import os
from app.core.imggen_core import ImageGenCore
from app.core.chat_message_core import ChatMessageCore
from app.core.embedder import Embedder
from app.core.retriever import Retriever
from app.core.vectordb import VectorDB
from app.models.imggen_model import GenerateImageRequest
from app.services.auth_core import auth_service
from datetime import datetime


router = APIRouter(prefix="/images", tags=["Images"])

chat_message_core = ChatMessageCore()
imggen_core = ImageGenCore(chat_message_core)
embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

retriever = Retriever(vectordb)


@router.post("/generate")
def generate_image(
    data: GenerateImageRequest,
    user=Depends(auth_service.get_current_user)
):
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    monthly_count = imggen_core.collection.count_documents({
        "user_id": user.id,
        "created_at": {"$gte": month_start}
    })

    if monthly_count >= 5:
        chat_message_core.save_message(
            chat_id=data.chat_id,
            user_id=user.id,
            role="user",
            content=data.query
        )

        chat_message_core.save_message(
            chat_id=data.chat_id,
            user_id=user.id,
            role="assistant",
            content="Monthly image generation limit reached (5 images per month)."
        )

        return {
            "success": False,
            "message": "Monthly image generation limit reached (5 images per month).",
            "fallback": "I can't generate images right now, but I can still explain or describe anything you'd like."
        }

    history = chat_message_core.get_messages(
        chat_id=data.chat_id,
        user_id=user.id,
        limit=10
    )

    chat_message_core.save_message(
        chat_id=data.chat_id,
        user_id=user.id,
        role="user",
        content=data.query
    )

    context = []

    try:
        if getattr(data, "mode", "normal") == "rag":
            context = retriever.retrieve(
                query=data.query,
                user_id=user.id,
                chat_id=data.chat_id,
                k=5
            )

        result = imggen_core.generate_image(
            query=data.query,
            user_id=user.id,
            chat_id=data.chat_id,
            history=history,
            context=context
        )

        return result

    except Exception as e:
        print("Image generation error:", str(e))

        chat_message_core.save_message(
            chat_id=data.chat_id,
            user_id=user.id,
            role="assistant",
            content="I can't generate images at this moment, but I can help explain anything you want."
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{image_id}")
def get_image(
    image_id: str,
    user=Depends(auth_service.get_current_user)
):
    image = imggen_core.get_image(
        image_id=image_id,
        user_id=user.id
    )

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return image

@router.get("/")
def list_images(user=Depends(auth_service.get_current_user)):
    return imggen_core.list_images(user_id=user.id)


@router.delete("/{image_id}")
def delete_image(image_id: str, user=Depends(auth_service.get_current_user)):
    deleted = imggen_core.delete_image(
        image_id=image_id,
        user_id=user.id
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"message": "Image deleted successfully"}
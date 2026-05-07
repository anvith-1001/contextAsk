import os
from fastapi import APIRouter, Depends
from app.core.vectordb import VectorDB
from app.core.embedder import Embedder
from app.services.auth_core import AuthService
from app.core.user_data_db import UserDataDB


router = APIRouter()
user_data_db = UserDataDB()
auth_service = AuthService()

embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

@router.get("/me")
def get_me(user=Depends(auth_service.get_current_user)):
    metadata = user.user_metadata or {}

    return {
        "id": user.id,
        "email": user.email,
        "name": metadata.get("name"),
        "dob": metadata.get("dob"),
        "avatar_url": metadata.get("avatar_url"),
        "auth_provider": user.app_metadata.get("provider") if user.app_metadata else None,
        "profile_completed": bool(
            metadata.get("profile_completed")
            and metadata.get("name")
            and metadata.get("dob")
        )
    }

@router.delete("/delete-account")
def delete_account(user=Depends(auth_service.get_current_user)):
    user_id = user.id

    deleted = user_data_db.delete_user_data(user_id)

    auth_service.delete_user(user_id)

    return {
        "message": "Account and all user data deleted",
        "deleted": deleted
    }
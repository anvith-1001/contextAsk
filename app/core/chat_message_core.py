from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os


class ChatMessageCore:

    def __init__(self):

        client = MongoClient(os.getenv("MONGO_URI"))

        db = client["rag_db"]

        self.collection = db["chat_messages"]

    def save_message(self, chat_id, user_id, role, content):

        message = {
            "chat_id": chat_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        }

        self.collection.insert_one(message)

    def get_messages(self, chat_id, user_id, limit=20):

        messages = self.collection.find(
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        ).sort("created_at", 1).limit(limit)

        results = []

        for msg in messages:
            results.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        return results

    def list_user_chats(self, user_id):

        chats = self.collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)

        results = []

        for chat in chats:
            results.append({
                "chat_id": str(chat["_id"]),
                "name": chat["name"],
                "mode": chat["mode"],
                "created_at": chat["created_at"]
            })

        return results

    def delete_chat(self, chat_id, user_id):

        chat = self.collection.find_one({
            "_id": ObjectId(chat_id),
            "user_id": user_id
        })

        if not chat:
            return False

        self.collection.delete_one({
            "_id": ObjectId(chat_id)
        })

        return True

chat_message_core = ChatMessageCore()
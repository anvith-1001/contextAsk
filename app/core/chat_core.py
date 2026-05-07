from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os


class ChatCore:

    def __init__(self):

        client = MongoClient(os.getenv("MONGO_URI"))

        db = client["rag_db"]

        self.collection = db["chat_sessions"]

    def create_chat(self, user_id, name, mode):

        chat = {
            "user_id": user_id,
            "name": name,
            "mode": mode,
            "created_at": datetime.utcnow()
        }

        result = self.collection.insert_one(chat)

        return {
            "chat_id": str(result.inserted_id),
            "name": name,
            "mode": mode
        }
    
    def update_chat_name(self, chat_id, user_id, name):

      result = self.collection.update_one(
          {
            "_id": ObjectId(chat_id),
            "user_id": user_id
          },
          {
            "$set": {
                "name": name
            }
          }
        )

      if result.matched_count == 0:
          return None

      return {
        "chat_id": chat_id,
        "name": name
      }
    
    
    def update_chat_mode(self, chat_id, user_id, mode):

        result = self.collection.update_one(
            {
                "_id": ObjectId(chat_id),
                "user_id": user_id
            },
            {
                "$set": {
                    "mode": mode
                }
            }
        )

        if result.matched_count == 0:
            return None

        chat = self.collection.find_one({
            "_id": ObjectId(chat_id),
            "user_id": user_id
        })

        return {
            "chat_id": str(chat["_id"]),
            "name": chat["name"],
            "mode": chat["mode"]
        }
    

    def get_chat(self, chat_id, user_id):

        chat = self.collection.find_one({
            "_id": ObjectId(chat_id),
            "user_id": user_id
        })

        if not chat:
            return None

        return {
            "chat_id": str(chat["_id"]),
            "name": chat["name"],
            "mode": chat.get("mode", "normal")
        }

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

chat_core = ChatCore()
from pymongo import MongoClient
import os

class UserDataDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["rag_db"]

    def delete_user_data(self, user_id: str):
        return {
            "chat_messages": self.db["chat_messages"]
                .delete_many({"user_id": user_id})
                .deleted_count,

            "chat_sessions": self.db["chat_sessions"]
                .delete_many({"user_id": user_id})
                .deleted_count,

            "doc": self.db["doc"]
                .delete_many({"user_id": user_id})
                .deleted_count,

            "generated_images": self.db["generated_images"]
                .delete_many({"user_id": user_id})
                .deleted_count,
        }
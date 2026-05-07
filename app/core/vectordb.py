from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

class VectorDB:
    def __init__(self, uri, db_name, collection_name, embedder):

        client = MongoClient(uri)

        collection = client[db_name][collection_name]

        self.store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embedder.model,
            index_name="vector_index"
        )

    def add(self, documents):
        self.store.add_documents(documents)

    def search(self, query, user_id, chat_id, k=5):

        return self.store.similarity_search(
       query=query,
       k=k,
       pre_filter={
        "$and": [
            {
                "user_id": user_id
            },
            {
                "chat_id": chat_id
            }
        ]
    }
)

# keyword search is removed in order to reduce latency.
    """ def keyword_search(self, query, user_id, k=5):

        results = self.store._collection.aggregate([
            {
                "$search": {
                    "index": "default",
                    "compound": {
                        "must": [
                            {
                                "text": {
                                    "query": query,
                                    "path": "text"
                                }
                            }
                        ],
                        "filter": [
                            {
                                "equals": {
                                    "path": "user_id",
                                    "value": user_id
                                }
                            }
                        ]
                    }
                }
            },
            {"$limit": k}
        ])

        docs = []

        for r in results:

            docs.append(
                Document(
                    page_content=r.get("text", ""),
                    metadata={
                        "source": r.get("metadata", {}).get("source"),
                        "user_id": r.get("metadata", {}).get("user_id")
                    }
                )
            )

        return docs
    """

    def delete_user_documents(self, user_id):
        self.store._collection.delete_many({
            "user_id": user_id
        })

    def delete_chat_documents(self, user_id, chat_id):
        self.store._collection.delete_many({
            "user_id": user_id,
            "chat_id": chat_id
        })
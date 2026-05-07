from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

class Indexer:
    def __init__(self, chunker, vectordb):
        self.chunker = chunker
        self.vectordb = vectordb

    def index_document(self, text: str, source: str, user_id, chat_id):
        chunks = self.chunker.chunk(text)

        documents = [
            Document(
                page_content=chunk,
                metadata={"source": source,
                          "user_id": user_id,
                          "chat_id": chat_id}
            )
            for chunk in chunks
        ]

        self.vectordb.add(documents)
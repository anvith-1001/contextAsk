from dotenv import load_dotenv
import os
from app.core.embedder import Embedder
from app.core.vectordb import VectorDB
from app.core.chunker import Chunker
from app.core.indexer import Indexer
from app.core.retriever import Retriever
from app.core.generator import Generator
from app.core.ragcore import RAGCore
from app.core.chat_message_core import chat_message_core

load_dotenv()


embedder = Embedder()

vectordb = VectorDB(
    uri=os.getenv("MONGO_URI"),
    db_name="rag_db",
    collection_name="doc",
    embedder=embedder
)

chunker = Chunker()
indexer = Indexer(chunker, vectordb)

retriever = Retriever(vectordb)
generator = Generator()

rag = RAGCore(
    retriever=retriever,
    generator=generator,
    chat_message_core=chat_message_core
)

user_id = "test_user_001"
chat_id = "test_chat_001"

sample_doc = """
Employees are entitled to 20 paid leave days annually.
Unused leaves expire after one year.
"""

indexer.index_document(
    text=sample_doc,
    source="leave_policy.pdf",
    user_id=user_id,
    chat_id=chat_id
)

result = rag.run(
    query="How many leave days are allowed?",
    user_id=user_id,
    chat_id=chat_id
)

print(result)
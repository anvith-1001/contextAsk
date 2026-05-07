import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

class Embedder:
    def __init__(self):
        self.model = GoogleGenerativeAIEmbeddings(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            model="models/gemini-embedding-001",
            output_dimensionality=512,
        )

    def embed(self, text: str):
        return self.model.embed_query(text)

    def embed_many(self, texts: list[str]):
        return self.model.embed_documents(texts)
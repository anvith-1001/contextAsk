from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes.document_routes import router as doc_router
from app.routes.rag_routes import router as ask_router
from app.routes.auth_route import router as auth_router
from app.routes.chat_route import router as chat_router
from app.routes.imggen_route import router as imggen_router
from fastapi.middleware.cors import CORSMiddleware
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(doc_router, prefix="/documents", tags=["Documents"])
app.include_router(ask_router, prefix="/ask", tags=["Ask"])
app.include_router(imggen_router, prefix="/images", tags=["Images"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
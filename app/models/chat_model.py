from pydantic import BaseModel
from typing import Optional

class CreateChatRequest(BaseModel):
    name: str
    mode: str  

class ChatResponse(BaseModel):
    chat_id: str
    name: str
    mode: str

class UpdateChatNameRequest(BaseModel):
    name: str
from pydantic import BaseModel
from typing import Optional

class GenerateImageRequest(BaseModel):
    chat_id: str
    query: str
    mode: Optional[str] = "normal"
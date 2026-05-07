from typing import List, Optional

from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    query: str
    chat_id: str
    relevant_doc_ids: Optional[List[str]] = Field(
        default=None,
        description="Ground-truth relevant chunk/document ids for retrieval evaluation."
    )
    baseline_latency_sec: Optional[float] = Field(
        default=None,
        description="Previous/baseline latency used to calculate latency reduction."
    )
    baseline_hallucination_rate: Optional[float] = Field(
        default=None,
        description="Previous hallucination rate from 0 to 1 used to calculate hallucination reduction."
    )
    user_satisfaction_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Optional user feedback score from 0 to 100."
    )
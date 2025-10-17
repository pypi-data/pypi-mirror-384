from typing import List, Optional
from pydantic import BaseModel

class WolframSolveResponse(BaseModel):
    rationale: str
    working_steps: List[str]
    answer: str


class WolframSolveRequest(BaseModel):
    question_text: str
    subject: Optional[str] = None
    app_id: Optional[str] = None
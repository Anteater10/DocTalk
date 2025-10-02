from pydantic import BaseModel
from typing import Optional, Dict, List
from .detect import Span

class SimplifyRequest(BaseModel):
    text: str
    spans: Optional[List[Span]] = None

class SimplifyResponse(BaseModel):
    text: str
    grade: float
    diagnostics: Dict[str, float] = {}

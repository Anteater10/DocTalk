from pydantic import BaseModel, Field
from typing import List, Literal, Optional

Category = Literal["diagnosis","procedure","medication","test","anatomy","measurement"]

class Span(BaseModel):
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)  # inclusive offset
    surface: str
    canonical: str
    category: Category
    negated: bool = False
    definition: Optional[str] = None
    why: Optional[str] = None
    ambiguous: Optional[bool] = None
    choices: Optional[List[str]] = None

class DetectRequest(BaseModel):
    text: str

class DetectResponse(BaseModel):
    spans: List[Span]

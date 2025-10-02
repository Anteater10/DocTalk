from pydantic import BaseModel
from typing import List, Literal

Label = Literal["diagnosis","test","plan","medication","other"]

class ClassifyRequest(BaseModel):
    sentences: List[str]

class ClassifyResponse(BaseModel):
    labels: List[Label]

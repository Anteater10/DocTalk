from pydantic import BaseModel

class SpellcheckRequest(BaseModel):
    text: str

class SpellcheckResponse(BaseModel):
    text: str

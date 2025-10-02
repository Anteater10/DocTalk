from fastapi import APIRouter
from ..schemas.spellcheck import SpellcheckRequest, SpellcheckResponse

router = APIRouter(prefix="/spellcheck", tags=["spellcheck"])

@router.post("", response_model=SpellcheckResponse)
def spellcheck(req: SpellcheckRequest) -> SpellcheckResponse:
    # Sprint 1: echo back. (Real correction comes later.)
    return SpellcheckResponse(text=req.text or "")

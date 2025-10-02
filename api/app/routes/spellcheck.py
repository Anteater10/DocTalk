from fastapi import APIRouter
from ..schemas.spellcheck import SpellcheckRequest, SpellcheckResponse

router = APIRouter(prefix="/spellcheck", tags=["spellcheck"])

@router.post("", response_model=SpellcheckResponse)
def spellcheck(req: SpellcheckRequest) -> SpellcheckResponse:
    return SpellcheckResponse(text=req.text or "")

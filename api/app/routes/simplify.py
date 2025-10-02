from fastapi import APIRouter
from ..schemas.simplify import SimplifyRequest, SimplifyResponse

router = APIRouter(prefix="/simplify", tags=["simplify"])

@router.post("", response_model=SimplifyResponse)
def simplify(req: SimplifyRequest) -> SimplifyResponse:
    text = (req.text or "").strip()
    if not text:
        simple = "This note explains your health in plain English."
    else:
        simple = f"Simplified: {text}"
    return SimplifyResponse(text=simple, grade=7.5, diagnostics={"sentences": 1.0})

from fastapi import APIRouter
from ..schemas.simplify import SimplifyRequest, SimplifyResponse

router = APIRouter(prefix="/simplify", tags=["simplify"])

@router.post("", response_model=SimplifyResponse)
def simplify(req: SimplifyRequest) -> SimplifyResponse:
    txt = (req.text or "").strip()
    return SimplifyResponse(
        text=f"Simplified: {txt}" if txt else "This note explains your health in plain English.",
        grade=7.5,
        diagnostics={"sentences": 1.0}
    )

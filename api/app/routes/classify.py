from fastapi import APIRouter
from ..schemas.classify import ClassifyRequest, ClassifyResponse

router = APIRouter(prefix="/classify", tags=["classify"])

@router.post("", response_model=ClassifyResponse)
def classify(req: ClassifyRequest) -> ClassifyResponse:
    # Sprint 1: label everything as "other" with matching length
    n = len(req.sentences or [])
    return ClassifyResponse(labels=["other"] * n)

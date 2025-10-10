from fastapi import APIRouter
from ..schemas.simplify import SimplifyRequest, SimplifyResponse
from app.nlp.rewrite.readability import flesch_kincaid_grade
from app.nlp.rewrite.rules import first_mention_expansions, apply_templates, shorten_long_sentences

router = APIRouter(prefix="/simplify", tags=["simplify"])

@router.post("", response_model=SimplifyResponse)
def simplify(req: SimplifyRequest) -> SimplifyResponse:
    raw = (req.text or "").strip()
    if not raw:
        return SimplifyResponse(
            text="This note explains your health in plain English.",
            grade=7.5,
            diagnostics={"sentences": 1.0, "words": 7.0, "syllables": 8.0},
        )

    with_expl = first_mention_expansions(raw, req.spans)
    templated = apply_templates(with_expl)
    simplified = shorten_long_sentences(templated, max_len=120)
    r = flesch_kincaid_grade(simplified)

    return SimplifyResponse(
        text=simplified,
        grade=float(r.fk_grade),
        diagnostics={
            "sentences": float(r.sentences),
            "words": float(r.words),
            "syllables": float(r.syllables),
        },
    )

from fastapi import APIRouter
from ..schemas.detect import DetectRequest, DetectResponse, Span
import re

router = APIRouter(prefix="/detect", tags=["detect"])

TROP_PAT = re.compile(r"\b(troponin)\b", re.IGNORECASE)
BP_PAT   = re.compile(r"\b(blood pressure)\b", re.IGNORECASE)

NEG_PHRASES = [
    "no troponin",
    "not troponin",
    "denies troponin",
    "negative for troponin",
    "no evidence of troponin",
    "no mention of troponin",
]

def is_negated_near(text: str, start: int, end: int) -> bool:
    # Check a small window around the match for simple negation phrases.
    w_start = max(0, start - 40)
    w_end = min(len(text), end + 40)
    window = text[w_start:w_end].lower()
    return any(p in window for p in NEG_PHRASES)

@router.post("", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    text = req.text or ""
    spans: list[Span] = []

    # 1) troponin (with basic negation)
    for m in TROP_PAT.finditer(text):
        s, e = m.start(1), m.end(1) - 1  # inclusive end
        neg = is_negated_near(text, s, e)
        spans.append(
            Span(
                start=s,
                end=e,
                surface=text[s:e+1],
                canonical="troponin",
                category="test",
                negated=neg,
                definition="A blood test for heart muscle injury.",
                why="High troponin can indicate a heart attack.",
            )
        )

    # 2) blood pressure (only if present and we didn't already add spans)
    if not spans:
        m = BP_PAT.search(text)
        if m:
            s, e = m.start(1), m.end(1) - 1
            spans.append(
                Span(
                    start=s,
                    end=e,
                    surface=text[s:e+1],
                    canonical="blood pressure",
                    category="measurement",
                    negated=False,
                    definition="The pressure of blood in the arteries.",
                    why="Very high or low values can be dangerous.",
                )
            )

    # 3) If nothing matched, return an empty list (no bogus offsets)
    return DetectResponse(spans=spans)

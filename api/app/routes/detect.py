from fastapi import APIRouter
from ..schemas.detect import DetectRequest, DetectResponse, Span
from typing import List, Dict
import re

# Pull aliases/terms from DB
from app.db.repo import alias_to_term_map

router = APIRouter(prefix="/detect", tags=["detect"])

NEG_PATTERNS = [
    "no {t}", "not {t}", "denies {t}", "negative for {t}",
    "no evidence of {t}", "no mention of {t}"
]

def is_negated_near(text: str, start: int, end: int, surface: str) -> bool:
    win = text[max(0, start-40):min(len(text), end+40)].lower()
    t = surface.lower()
    return any(p.format(t=t) in win for p in NEG_PATTERNS)

def build_pattern_and_meta() -> tuple[re.Pattern, Dict[str, Dict]]:
    """
    Build a regex from all aliases in DB.
    Returns (compiled_pattern, alias_metadata).
    """
    alias_map = alias_to_term_map()  # { alias_lower: {canonical, category, definition, why} }
    aliases = sorted(alias_map.keys(), key=len, reverse=True)
    if not aliases:
        return re.compile(r"(?!x)x"), alias_map  # match nothing if empty
    pat = re.compile(r"\b(" + "|".join(map(re.escape, aliases)) + r")\b", re.IGNORECASE)
    return pat, alias_map

PAT, META = build_pattern_and_meta()

@router.post("", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    text = req.text or ""
    spans: List[Span] = []

    for m in PAT.finditer(text):
        s, e = m.start(1), m.end(1) - 1  # inclusive end
        surf = text[s:e+1]
        key = m.group(1).lower()
        meta = META.get(key)
        if not meta:
            continue
        spans.append(Span(
            start=s, end=e,
            surface=surf,
            canonical=meta["canonical"],
            category=meta["category"],
            negated=is_negated_near(text, s, e, surf),
            definition=meta.get("definition"),
            why=meta.get("why"),
        ))

    # Drop overlaps (keep longest-first)
    spans.sort(key=lambda sp: (sp.start, -(sp.end - sp.start + 1)))
    filtered: List[Span] = []
    last_end = -1
    for sp in spans:
        if sp.start > last_end:
            filtered.append(sp)
            last_end = sp.end
    return DetectResponse(spans=filtered)

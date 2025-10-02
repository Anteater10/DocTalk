from fastapi import APIRouter
from ..schemas.detect import DetectRequest, DetectResponse, Span
import re
from typing import List, Dict

router = APIRouter(prefix="/detect", tags=["detect"])

# Mini in-memory glossary for Sprint 1 demo
GLOSSARY: Dict[str, Dict] = {
    "troponin":      {"canonical": "troponin", "category": "test",
                      "definition": "Blood marker of heart muscle injury.",
                      "why": "High levels can indicate a heart attack."},
    "blood pressure":{"canonical": "blood pressure", "category": "measurement",
                      "definition": "Pressure of blood in the arteries.",
                      "why": "Very high or low values can be dangerous."},
    "glucose":       {"canonical": "glucose", "category": "test",
                      "definition": "Sugar level in blood.",
                      "why": "High levels suggest diabetes risk."},
    "hemoglobin a1c":{"canonical": "hemoglobin A1c", "category": "test",
                      "definition": "Average blood sugar over ~3 months.",
                      "why": "Used to diagnose and monitor diabetes."},
    "aspirin":       {"canonical": "aspirin", "category": "medication",
                      "definition": "Pain reliever that thins blood.",
                      "why": "Used after heart events to prevent clots."},
    "metformin":     {"canonical": "metformin", "category": "medication",
                      "definition": "Medicine to lower blood sugar.",
                      "why": "First-line therapy for type 2 diabetes."},
    "mri":           {"canonical": "MRI", "category": "procedure",
                      "definition": "Imaging that uses magnets—not radiation.",
                      "why": "Shows soft tissues, brain, joints, etc."},
    "pneumonia":     {"canonical": "pneumonia", "category": "diagnosis",
                      "definition": "Infection of the lungs.",
                      "why": "Needs antibiotics and close monitoring."},
}

# Build one regex that matches the longest phrases first
ALIASES = sorted(GLOSSARY.keys(), key=len, reverse=True)
PAT = re.compile(r"\b(" + "|".join(map(re.escape, ALIASES)) + r")\b", re.IGNORECASE)

NEG_PATTERNS = [
    "no {t}", "not {t}", "denies {t}", "negative for {t}",
    "no evidence of {t}", "no mention of {t}"
]

def is_negated_near(text: str, start: int, end: int, surface: str) -> bool:
    win = text[max(0, start-40):min(len(text), end+40)].lower()
    t = surface.lower()
    return any(p.format(t=t) in win for p in NEG_PATTERNS)

@router.post("", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    text = req.text or ""
    spans: List[Span] = []

    for m in PAT.finditer(text):
        s, e = m.start(1), m.end(1) - 1  # inclusive end
        surf = text[s:e+1]
        key = m.group(1).lower()
        meta = GLOSSARY[key]
        spans.append(Span(
            start=s, end=e,
            surface=surf,
            canonical=meta["canonical"],
            category=meta["category"],
            negated=is_negated_near(text, s, e, surf),
            definition=meta["definition"],
            why=meta["why"],
        ))

    # Sort by (start, -length) and drop overlaps (keep longest first)
    spans.sort(key=lambda sp: (sp.start, -(sp.end - sp.start + 1)))
    filtered: List[Span] = []
    last_end = -1
    for sp in spans:
        if sp.start > last_end:
            filtered.append(sp)
            last_end = sp.end
    return DetectResponse(spans=filtered)

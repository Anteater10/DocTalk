from __future__ import annotations
import os
from typing import List, Tuple
import spacy

# Change via env var if you switch models
NLP_MODEL = os.getenv("SCISPACY_MODEL", "en_core_sci_sm")
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(NLP_MODEL, disable=["lemmatizer", "tok2vec", "attribute_ruler"])
    return _nlp

# Map scispaCy labels to DocTalk categories (extend as needed)
LABEL_MAP = {
    "DISEASE": "diagnosis",
    "SYMPTOM": "diagnosis",
    "CHEMICAL": "medication",
    "DRUG": "medication",
    "TEST": "test",
    "LAB_VALUE": "measurement",
    "ANATOMICAL_SYSTEM": "anatomy",
    "ORGAN": "anatomy",
}

def ner_spans(text: str) -> List[Tuple[int, int, str, str]]:
    """Return list of (start, end_inclusive, surface, category)."""
    if not text:
        return []
    doc = get_nlp()(text)
    out: List[Tuple[int, int, str, str]] = []
    for ent in doc.ents:
        cat = LABEL_MAP.get(ent.label_)
        if not cat:
            continue
        out.append((ent.start_char, ent.end_char - 1, ent.text, cat))
    return out

# app/routes/detect.py
from __future__ import annotations
from fastapi import APIRouter
from typing import List, Dict, Tuple
import os
import re

from ..schemas.detect import DetectRequest, DetectResponse, Span

# DB-backed glossary/alias lookup
from app.db.repo import alias_to_term_map

# Negation
from app.nlp.detect.negation import is_negated as negation_is_negated

# Acronym resolver (Phase 2)
from app.nlp.detect.acronym_resolver import (
    extract_parenthetical_map, load_doc_map, save_choice,
    apply_map_to_spans, inject_acronym_spans
)

router = APIRouter(prefix="/detect", tags=["detect"])

def build_pattern_and_meta() -> Tuple[re.Pattern, Dict[str, Dict]]:
    """
    Build a case-insensitive regex that matches any alias or canonical term.
    Returns (compiled_pattern, alias_metadata)

    alias_metadata: { alias_lower: {canonical, category, definition, why} }
    """
    alias_map = alias_to_term_map()
    aliases = sorted(alias_map.keys(), key=len, reverse=True)
    if not aliases:
        # empty regex that matches nothing
        return re.compile(r"(?!x)x"), alias_map
    pat = re.compile(r"\b(" + "|".join(map(re.escape, aliases)) + r")\b", re.IGNORECASE)
    return pat, alias_map

PAT, META = build_pattern_and_meta()

# Feature flag for NER (we import lazily to avoid spaCy import errors)
USE_NER = os.getenv("USE_NER", "0") == "1"

def iter_ner_spans(text: str):
    """Yield (start, end, surface, category) from scispaCy if enabled."""
    if not USE_NER:
        return
    try:
        from app.nlp.detect.spacy_ner import ner_spans
    except Exception:
        return
    for s, e, surf, cat in ner_spans(text):
        yield s, e, surf, cat


@router.post("", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    """
    Hybrid detector:
      1) Glossary-based longest-match using DB aliases (precise).
      2) Learn acronyms from parentheses, persist per doc, inject later ACR mentions.
      3) Cue-based negation check within a small text window.
      4) Optional scispaCy NER augmentation (if USE_NER=1).
      5) Deterministic overlap resolution (prefer earliest + longest span).
    """
    text = req.text or ""
    spans: List[Span] = []

    # ---- 1) Glossary pass ----
    for m in PAT.finditer(text):
        s, e = m.start(1), m.end(1) - 1  # inclusive end
        surf = text[s:e+1]
        key = m.group(1).lower()
        meta = META.get(key)
        if not meta:
            continue
        spans.append(
            Span(
                start=s,
                end=e,
                surface=surf,
                canonical=meta["canonical"],
                category=meta["category"],
                negated=negation_is_negated(text, s, e),
                definition=meta.get("definition"),
                why=meta.get("why"),
            )
        )

    # ---- 2) Phase 2: acronym learning + injection ----
    doc_uuid = getattr(req, "doc_uuid", None)

    # Learn “longform (ACR)” from this text if longform is in glossary META
    parenthetical_map = extract_parenthetical_map(text, META)

    # Persist what we learned for this doc
    if doc_uuid:
        for acr, canon in parenthetical_map.items():
            save_choice(doc_uuid, acr, canon)

    # Merge with previously learned mappings for this doc
    doc_map = load_doc_map(doc_uuid)
    doc_map.update(parenthetical_map)

    # Apply map to any acronym spans we already have
    apply_map_to_spans(spans, doc_map, META)

    # Inject new spans for plain ACR tokens not already covered
    injected = inject_acronym_spans(text, doc_map, spans, META, negation_is_negated)
    spans.extend(injected)

    # ---- De-overlap (keep earliest, prefer longer) ----
    spans.sort(key=lambda sp: (sp.start, -(sp.end - sp.start + 1)))
    filtered: List[Span] = []
    last_end = -1
    for sp in spans:
        if sp.start > last_end:
            filtered.append(sp)
            last_end = sp.end

    # ---- 4) Optional NER augmentation (skip overlaps) ----
    if USE_NER and text:
        for s, e, surf, cat in iter_ner_spans(text) or []:
            if any(not (e < g.start or s > g.end) for g in filtered):
                continue
            filtered.append(
                Span(
                    start=s,
                    end=e,
                    surface=surf,
                    canonical=surf,
                    category=cat,
                    negated=negation_is_negated(text, s, e),
                )
            )
        # Final overlap pass (in case NER spans overlap each other)
        filtered.sort(key=lambda sp: (sp.start, -(sp.end - sp.start + 1)))
        final: List[Span] = []
        last_end = -1
        for sp in filtered:
            if sp.start > last_end:
                final.append(sp)
                last_end = sp.end
        return DetectResponse(spans=final)

    return DetectResponse(spans=filtered)

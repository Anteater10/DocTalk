from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional

# Persist per-document acronym choices in a simple JSON file
MEMO_PATH = Path(__file__).parents[2] / "data" / "acronym_memory.json"
MEMO_PATH.parent.mkdir(parents=True, exist_ok=True)

def _load_all() -> Dict[str, Dict[str, str]]:
    if not MEMO_PATH.exists():
        return {}
    try:
        return json.loads(MEMO_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_all(data: Dict[str, Dict[str, str]]) -> None:
    MEMO_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_doc_map(doc_uuid: Optional[str]) -> Dict[str, str]:
    """Return previously learned acronym→canonical map for a document."""
    if not doc_uuid:
        return {}
    all_maps = _load_all()
    return dict(all_maps.get(doc_uuid, {}))

def save_choice(doc_uuid: Optional[str], acronym: str, canonical: str) -> None:
    """Persist a learned mapping ACRONYM -> canonical for this document."""
    if not doc_uuid:
        return
    all_maps = _load_all()
    d = all_maps.get(doc_uuid, {})
    d[acronym.upper()] = canonical
    all_maps[doc_uuid] = d
    _save_all(all_maps)

def extract_parenthetical_map(text: str, meta: Dict[str, Dict]) -> Dict[str, str]:
    """
    Learn mappings from patterns like 'myocardial infarction (MI)'.
    Only accept if the longform exists in META (so we know category/definition).
    Returns { 'MI': 'myocardial infarction', ... }
    """
    out: Dict[str, str] = {}
    pat = re.compile(r"\b([A-Za-z][A-Za-z0-9 /\-]{2,})\s*\(\s*([A-Z]{2,10})\s*\)")
    for m in pat.finditer(text):
        longform = m.group(1).strip()
        acr = m.group(2).upper()
        lf_key = longform.lower()
        if lf_key in meta:
            canonical = meta[lf_key]["canonical"]
            out[acr] = canonical
    return out

def _find_word_spans(text: str, token: str) -> List[Tuple[int, int, str]]:
    spans: List[Tuple[int, int, str]] = []
    for m in re.finditer(rf"\b({re.escape(token)})\b", text, flags=re.IGNORECASE):
        s, e = m.start(1), m.end(1) - 1
        spans.append((s, e, m.group(1)))
    return spans

def _overlaps(s: int, e: int, existing: Iterable[Tuple[int, int]]) -> bool:
    for (a, b) in existing:
        if not (e < a or s > b):
            return True
    return False

def apply_map_to_spans(spans: List, doc_map: Dict[str, str], meta: Dict[str, Dict]) -> None:
    """If a span surface is an acronym we know, fill in its canonical/metadata."""
    if not doc_map:
        return
    for sp in spans:
        acr = sp.surface.upper()
        if acr in doc_map:
            canon = doc_map[acr]
            m = meta.get(canon.lower())
            if m:
                sp.canonical = m["canonical"]
                sp.category = m["category"]
                sp.definition = m.get("definition")
                sp.why = m.get("why")

def inject_acronym_spans(text: str,
                         doc_map: Dict[str, str],
                         existing_spans: List,
                         meta: Dict[str, Dict],
                         negation_fn) -> List:
    """Add new spans for plain acronym tokens using the learned doc_map."""
    injected = []
    if not doc_map:
        return injected

    occupied = [(sp.start, sp.end) for sp in existing_spans]

    for acr, canon in doc_map.items():
        m = meta.get(canon.lower())
        if not m:
            continue
        for s, e, surf in _find_word_spans(text, acr):
            if _overlaps(s, e, occupied):
                continue
            neg = bool(negation_fn(text, s, e))
            from app.schemas.detect import Span  # avoid circular import at import time
            injected.append(
                Span(
                    start=s,
                    end=e,
                    surface=surf,
                    canonical=m["canonical"],
                    category=m["category"],
                    negated=neg,
                    definition=m.get("definition"),
                    why=m.get("why"),
                )
            )
            occupied.append((s, e))

    injected.sort(key=lambda sp: (sp.start, -(sp.end - sp.start + 1)))
    out = []
    last = -1
    for sp in injected:
        if sp.start > last:
            out.append(sp)
            last = sp.end
    return out

from __future__ import annotations
import re
from typing import List, Tuple, Optional
from app.schemas.detect import Span

TEMPLATES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bfindings indicate\b", re.I), "This means"),
    (re.compile(r"\brecommend(?:ed)?\b", re.I), "We suggest"),
    (re.compile(r"\bpatient\b", re.I), "You"),
    (re.compile(r"\bdenies\b", re.I), "does not have"),
]

def apply_templates(text: str) -> str:
    out = text
    for pat, repl in TEMPLATES:
        out = pat.sub(repl, out)
    out = re.sub(r";\s*", ". ", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out

def first_mention_expansions(text: str, spans: Optional[List[Span]]) -> str:
    if not spans:
        return text
    seen = set()
    replacements: List[Tuple[int,int,str]] = []
    for sp in sorted(spans, key=lambda s: s.start):
        canon = sp.canonical.lower().strip()
        if not sp.definition or canon in seen:
            continue
        seen.add(canon)
        surface = text[sp.start:sp.end+1]
        expl = f"{surface} ({sp.definition})"
        replacements.append((sp.start, sp.end, expl))
    if not replacements:
        return text
    out = []
    idx = 0
    for s, e, repl in replacements:
        out.append(text[idx:s])
        out.append(repl)
        idx = e + 1
    out.append(text[idx:])
    return "".join(out)

def shorten_long_sentences(text: str, max_len: int = 120) -> str:
    parts = re.split(r'([.!?])', text)
    chunks = []
    for i in range(0, len(parts), 2):
        sent = (parts[i] or "").strip()
        punct = parts[i+1] if i+1 < len(parts) else "."
        if not sent:
            continue
        if len(sent) <= max_len:
            chunks.append(sent + punct)
        else:
            # prefer comma splits, fallback to words
            raw = [p.strip() for p in sent.split(",") if p.strip()]
            segments = raw or sent.split()
            acc = []
            cur = ""
            for seg in segments:
                add = seg.replace(",", "")
                nxt = (cur + " " + add).strip()
                if len(nxt) > max_len and cur:
                    acc.append(cur + ".")
                    cur = add
                else:
                    cur = nxt
            if cur:
                acc.append(cur + ".")
            chunks.extend(acc)
    return " ".join(chunks).strip()

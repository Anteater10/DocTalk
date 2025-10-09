from typing import Iterable
import re

# Cues that should appear BEFORE the term
PRE_CUES: Iterable[str] = (
    "no", "not", "denies", "without", "absence of", "free of"
)
# Cues that commonly appear BEFORE the term as a phrase: "negative for X"
PHRASE_CUES: Iterable[str] = ("negative for",)

_SENT_SPLIT = re.compile(r'([.!?])')  # light sentence splitter

def _sentence_bounds(text: str, idx: int) -> tuple[int, int]:
    """Return (start,end) char bounds of the sentence containing idx."""
    # naive: split by punctuation and track offsets
    parts = _SENT_SPLIT.split(text)
    start = 0
    pos = 0
    for i in range(0, len(parts), 2):
        sent = parts[i]
        end = pos + len(sent)
        # include trailing punctuation chunk if present
        if i + 1 < len(parts):
            end += len(parts[i+1])
        if pos <= idx < end:
            return pos, end
        pos = end
    return 0, len(text)

def is_negated(text: str, start: int, end: int, window_tokens: int = 8) -> bool:
    """
    Heuristic negation:
      - Restrict search to the CURRENT sentence only.
      - For PRE_CUES: cue must be BEFORE the term and within ~window_tokens.
      - Allow phrase cues like "negative for X" where cue is before the span.
    """
    t = text.lower()
    s_start, s_end = _sentence_bounds(t, start)
    sent = t[s_start:s_end]

    # left context only (directional): from sentence start to term start
    left = t[s_start:start]

    # quick token window (approx): check last N tokens of left context
    tokens = re.findall(r"\w+|[^\w\s]", left)
    last_n = " ".join(tokens[-window_tokens:]) if tokens else left

    # phrase cues (like "negative for") anywhere in left context
    if any(pc in left for pc in PHRASE_CUES):
        return True

    # pre-cues in the last-N-tokens window
    return any(re.search(rf"\b{re.escape(cue)}\b", last_n) for cue in PRE_CUES)

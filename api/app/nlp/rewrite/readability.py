from __future__ import annotations
import re
from dataclasses import dataclass

_SENT_SPLIT = re.compile(r'[.!?]+(?=\s|$)')
_WORD_RE = re.compile(r"[A-Za-z']+")
_VOWELS = set("aeiouy")

def _count_sentences(text: str) -> int:
    s = [m.group(0) for m in _SENT_SPLIT.finditer(text)]
    return max(1, len(s)) if s else 1

def _words(text: str):
    return _WORD_RE.findall(text)

def _count_syllables_in_word(w: str) -> int:
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return 0
    groups = 0
    prev_v = False
    for ch in w:
        v = ch in _VOWELS
        if v and not prev_v:
            groups += 1
        prev_v = v
    if w.endswith("e") and groups > 1:
        groups -= 1
    return max(1, groups)

def _count_syllables(words) -> int:
    return sum(_count_syllables_in_word(w) for w in words)

@dataclass
class ReadabilityResult:
    sentences: int
    words: int
    syllables: int
    fk_grade: float

def flesch_kincaid_grade(text: str) -> ReadabilityResult:
    words = _words(text)
    n_words = max(1, len(words))
    n_sent = _count_sentences(text)
    n_syll = _count_syllables(words)
    fk = 0.39 * (n_words / n_sent) + 11.8 * (n_syll / n_words) - 15.59
    return ReadabilityResult(sentences=n_sent, words=n_words, syllables=n_syll, fk_grade=round(fk, 2))

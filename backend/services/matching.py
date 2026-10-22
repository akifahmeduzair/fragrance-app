"""
Matches an AI-read brand/name against our own dataset.

The old matcher compared one long "brand + name" string with a low cutoff, so an
unknown fragrance (e.g. "Zimaya Mazaaj Infused") could be matched to an unrelated
one ("Zara Man Silver"). This version scores brand and name separately and needs
both to be close.

Flankers (Sauvage vs Sauvage Elixir, Acqua di Gio vs Acqua di Gio Profondo) are
different fragrances, so the name must match exactly once concentration and
gender words are ignored. A small typo tolerance is the only slack allowed.
"""
from __future__ import annotations

import difflib
import re
from typing import Optional

BRAND_MIN = 0.75
NAME_MIN = 0.85

_REPLACEMENTS = [
    (r"eau de parfum", "edp"),
    (r"eau de toilette", "edt"),
    (r"extrait de parfum", "extrait"),
    (r"\bparfum\b", "edp"),
]
# Words that describe concentration or target gender, not a different fragrance.
_IGNORED_IN_NAME = {"by", "for", "men", "women", "him", "her", "pour", "homme", "femme",
                    "edp", "edt", "extrait", "cologne"}


def _norm(text: str) -> str:
    text = (text or "").lower()
    for pattern, repl in _REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return re.sub(r"[^a-z0-9 ]+", " ", text).strip()


def _brand_score(guess: str, actual: str) -> float:
    a, b = _norm(guess), _norm(actual)
    if not a or not b:
        return 0.0
    ta, tb = set(a.split()), set(b.split())
    if ta <= tb or tb <= ta:  # "Dior" vs "Christian Dior", "Armani" vs "Giorgio Armani"
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _name_score(guess: str, actual: str) -> float:
    ta = [t for t in _norm(guess).split() if t not in _IGNORED_IN_NAME]
    tb = [t for t in _norm(actual).split() if t not in _IGNORED_IN_NAME]
    if not ta or not tb:
        return 0.0
    if set(ta) == set(tb):
        return 1.0
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()


def best_match(brand: str, name: str, fragrances: list[dict]) -> Optional[tuple[dict, float]]:
    """Return (fragrance, confidence) if both brand and name are close enough, else None."""
    if not (brand or "").strip() or not (name or "").strip():
        return None

    best: Optional[tuple[dict, float]] = None
    for f in fragrances:
        brand_score = _brand_score(brand, f["brand"])
        name_score = _name_score(name, f["name"])
        if brand_score < BRAND_MIN or name_score < NAME_MIN:
            continue
        score = (brand_score + name_score) / 2
        if best is None or score > best[1]:
            best = (f, score)
    return best

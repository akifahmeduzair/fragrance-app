"""
Similarity engine for fragrances.

Approach (classical baseline, no external model downloads needed):
- Represent each fragrance as a "scent document": its accords + top/heart/base
  notes, each repeated a few times to weight them relative to each other.
- Vectorize all scent documents with TF-IDF.
- Cosine similarity between vectors = scent similarity score (0-1).

This is intentionally the "classical" side of the classical-vs-embeddings
comparison mentioned in the project abstract. Swapping in a sentence-embedding
model later only requires replacing `_vectorize()` and `similarity_matrix`.
"""
from __future__ import annotations

from typing import Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _scent_document(fragrance: dict) -> str:
    """Turn a fragrance record into a weighted bag-of-terms string."""
    accords = fragrance.get("accords", [])
    notes = fragrance.get("notes", {})
    top = notes.get("top", [])
    heart = notes.get("heart", [])
    base = notes.get("base", [])

    terms: list[str] = []
    # Accords carry the most signal about overall "smell family" -> weight x3
    for a in accords:
        terms += [a.replace(" ", "_")] * 3
    # Heart/base notes define the lasting character -> weight x2
    for n in heart:
        terms += [n.replace(" ", "_")] * 2
    for n in base:
        terms += [n.replace(" ", "_")] * 2
    # Top notes fade fastest -> weight x1
    for n in top:
        terms += [n.replace(" ", "_")]

    return " ".join(terms)


class SimilarityEngine:
    def __init__(self, fragrances: list[dict]):
        self.fragrances = fragrances
        self.ids = [f["id"] for f in fragrances]
        self._id_to_index = {fid: i for i, fid in enumerate(self.ids)}

        documents = [_scent_document(f) for f in fragrances]
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(documents)
        self.sim_matrix = cosine_similarity(self.matrix)

    def similar_to(self, fragrance_id: str, top_n: int = 5, exclude_self: bool = True) -> list[dict]:
        idx = self._id_to_index.get(fragrance_id)
        if idx is None:
            return []
        scores = self.sim_matrix[idx]
        order = np.argsort(-scores)
        results = []
        for i in order:
            if exclude_self and self.ids[i] == fragrance_id:
                continue
            results.append({"fragrance": self.fragrances[i], "score": round(float(scores[i]), 4)})
            if len(results) >= top_n:
                break
        return results

    def score_between(self, id_a: str, id_b: str) -> Optional[float]:
        ia = self._id_to_index.get(id_a)
        ib = self._id_to_index.get(id_b)
        if ia is None or ib is None:
            return None
        return round(float(self.sim_matrix[ia][ib]), 4)

    def check_against_collection(self, candidate_id: str, owned_ids: list[str], threshold: float = 0.55) -> list[dict]:
        """Return owned fragrances that are similar enough to the candidate to flag."""
        flags = []
        for owned_id in owned_ids:
            if owned_id == candidate_id:
                continue
            score = self.score_between(candidate_id, owned_id)
            if score is not None and score >= threshold:
                idx = self._id_to_index[owned_id]
                flags.append({"fragrance": self.fragrances[idx], "score": score})
        flags.sort(key=lambda f: -f["score"])
        return flags

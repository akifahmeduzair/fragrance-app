from __future__ import annotations

import json
import os
import difflib
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.similarity import SimilarityEngine
from services.gemini_service import identify_from_image, lookup_details
from services.matching import best_match

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "fragrances.json"
INVENTORY_PATH = BASE_DIR / "data" / "inventory.json"

app = FastAPI(title="Fragrance? API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(DATA_PATH, "r") as f:
    FRAGRANCES: list[dict] = json.load(f)

FRAGRANCES_BY_ID = {f["id"]: f for f in FRAGRANCES}
engine = SimilarityEngine(FRAGRANCES)


def _load_inventory() -> list[str]:
    if INVENTORY_PATH.exists():
        with open(INVENTORY_PATH, "r") as f:
            return json.load(f)
    return []


def _save_inventory(ids: list[str]) -> None:
    with open(INVENTORY_PATH, "w") as f:
        json.dump(ids, f)


def _public(fragrance: dict) -> dict:
    """Fragrance record plus its dupe/inspired-by relationships resolved to names."""
    out = dict(fragrance)
    inspired_by_id = fragrance.get("inspired_by")
    out["inspired_by"] = FRAGRANCES_BY_ID.get(inspired_by_id) if inspired_by_id else None
    out["dupes"] = [FRAGRANCES_BY_ID[d] for d in fragrance.get("dupes", []) if d in FRAGRANCES_BY_ID]
    return out


@app.get("/api/fragrances")
def list_fragrances():
    return [_public(f) for f in FRAGRANCES]


@app.get("/api/fragrances/search")
def search_fragrances(q: str):
    q_lower = q.lower().strip()
    if not q_lower:
        return []
    scored = []
    for f in FRAGRANCES:
        haystack = f"{f['brand']} {f['name']}".lower()
        if q_lower in haystack:
            scored.append((1.0, f))
        else:
            ratio = difflib.SequenceMatcher(None, q_lower, haystack).ratio()
            if ratio > 0.4:
                scored.append((ratio, f))
    scored.sort(key=lambda x: -x[0])
    return [_public(f) for _, f in scored[:10]]


@app.get("/api/fragrances/{fragrance_id}")
def get_fragrance(fragrance_id: str):
    f = FRAGRANCES_BY_ID.get(fragrance_id)
    if not f:
        raise HTTPException(404, "Fragrance not found")
    result = _public(f)
    result["similar"] = engine.similar_to(fragrance_id, top_n=5)
    return result


def _best_match(brand: str, name: str) -> Optional[dict]:
    found = best_match(brand, name, FRAGRANCES)
    if not found:
        return None
    fragrance, score = found
    return {"match": _public(fragrance), "match_confidence": round(score, 3)}


@app.post("/api/identify")
async def identify(image: UploadFile = File(...)):
    """
    Pipeline:
      1. Send the photo to Gemini -> get a brand/name guess (vision is good at this).
      2. Fuzzy-match that guess against OUR OWN dataset (grounded facts).
      3. Return both the raw AI guess and the grounded record, so the UI can
         show "here's what we think it is" + a confirm step, never inventing notes.
    """
    image_bytes = await image.read()
    try:
        guess = identify_from_image(image_bytes, mime_type=image.content_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    matched = _best_match(guess.get("brand", ""), guess.get("name", ""))
    return {
        "ai_guess": guess,
        "grounded_match": matched,
    }


class LookupRequest(BaseModel):
    brand: str
    name: str


@app.post("/api/lookup")
def lookup(payload: LookupRequest):
    """
    Fallback for a fragrance that is not in our dataset: web-grounded notes with
    sources, flagged unverified. Refuses names that DO match the dataset, so the
    dataset stays the only source for fragrances it covers.
    """
    brand, name = payload.brand.strip(), payload.name.strip()
    if not brand or not name:
        raise HTTPException(400, "Both brand and name are required.")
    if _best_match(brand, name):
        raise HTTPException(409, "This fragrance is in the dataset; use /api/fragrances instead.")
    try:
        return lookup_details(brand, name)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:  # network/quota/model errors from the Gemini SDK
        raise HTTPException(502, f"Web lookup failed: {e}")


class InventoryAdd(BaseModel):
    fragrance_id: str


@app.get("/api/inventory")
def get_inventory():
    ids = _load_inventory()
    return [_public(FRAGRANCES_BY_ID[i]) for i in ids if i in FRAGRANCES_BY_ID]


@app.post("/api/inventory")
def add_to_inventory(payload: InventoryAdd):
    if payload.fragrance_id not in FRAGRANCES_BY_ID:
        raise HTTPException(404, "Fragrance not found")
    ids = _load_inventory()
    if payload.fragrance_id not in ids:
        ids.append(payload.fragrance_id)
        _save_inventory(ids)
    return {"inventory": ids}


@app.delete("/api/inventory/{fragrance_id}")
def remove_from_inventory(fragrance_id: str):
    ids = _load_inventory()
    ids = [i for i in ids if i != fragrance_id]
    _save_inventory(ids)
    return {"inventory": ids}


@app.get("/api/check/{fragrance_id}")
def check_duplicate(fragrance_id: str):
    """Does this fragrance smell too similar to something already owned?"""
    if fragrance_id not in FRAGRANCES_BY_ID:
        raise HTTPException(404, "Fragrance not found")
    owned = _load_inventory()
    flags = engine.check_against_collection(fragrance_id, owned)
    return {"fragrance_id": fragrance_id, "flags": flags}


@app.get("/api/health")
def health():
    return {"status": "ok", "fragrances_loaded": len(FRAGRANCES), "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY"))}

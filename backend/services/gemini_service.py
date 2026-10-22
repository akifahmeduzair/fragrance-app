"""
Gemini calls, kept separate from the grounded dataset.

identify_from_image: "what fragrance is in this photo?" Only brand/name is asked
for here, never notes. For fragrances in our dataset, notes/accords/dupes always
come from the dataset (see similarity.py + main.py).

lookup_details: fallback for fragrances NOT in the dataset. Uses Google Search
grounding (not model memory), returns the sources it used, and is shown to the
user as unverified.
"""
from __future__ import annotations

import json
import os
from google import genai
from google.genai import types

_PROMPT = """You are looking at a photo of a perfume/cologne bottle or box.
Identify the brand and fragrance name as precisely as you can from the label,
bottle shape, and box design. If you can also tell the concentration
(EDT/EDP/Parfum) or a size, include it, otherwise leave it blank.

Respond with ONLY a JSON object, no markdown fences, in this exact shape:
{"brand": "...", "name": "...", "concentration": "", "confidence": 0.0}

confidence should be your own 0-1 estimate of how sure you are.
If you cannot identify it at all, return brand and name as empty strings."""


def identify_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Export it before starting the backend, "
            "e.g. export GEMINI_API_KEY=your_key_here"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            _PROMPT,
        ],
    )

    parsed = _parse_json_object(response.text) or {}
    parsed.setdefault("brand", "")
    parsed.setdefault("name", "")
    parsed.setdefault("concentration", "")
    parsed.setdefault("confidence", 0.0)
    return parsed


# ---------------------------------------------------------------------------
# Fallback: fragrances that are NOT in our dataset
# ---------------------------------------------------------------------------
# Here Gemini is NOT answering from memory. It is given the Google Search tool and
# told to report only what it finds on the web, and the pages it used come back as
# `sources` so the UI can show them. The result is still unverified, and the UI
# says so. Dataset matches never go through this path.

_LOOKUP_PROMPT = """Use Google Search to find the scent notes for this fragrance:
Brand: {brand}
Name: {name}

Report only what you find on the web. Do not guess or fill gaps from memory.
If you cannot find reliable notes for this exact fragrance (not a similarly named
flanker), set "found" to false and leave the lists empty.

Respond with ONLY a JSON object, no markdown fences, in this exact shape:
{{"found": true, "brand": "", "name": "", "concentration": "", "year": null,
  "gender": "", "accords": [], "notes": {{"top": [], "heart": [], "base": []}},
  "inspired_by": null, "summary": ""}}

"inspired_by" is the name of the fragrance this one is said to be a clone or dupe
of, or null. "summary" is one sentence describing how it smells."""


def _parse_json_object(text: str | None) -> dict | None:
    """Pull the first JSON object out of a model reply, tolerating code fences and chatter."""
    if not text:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def _normalize_lookup(parsed: dict | None, brand: str, name: str) -> dict:
    parsed = parsed or {}
    notes = parsed.get("notes") if isinstance(parsed.get("notes"), dict) else {}
    result = {
        "found": bool(parsed.get("found")),
        "brand": str(parsed.get("brand") or brand),
        "name": str(parsed.get("name") or name),
        "concentration": str(parsed.get("concentration") or ""),
        "year": parsed.get("year") if isinstance(parsed.get("year"), int) else None,
        "gender": str(parsed.get("gender") or ""),
        "accords": _clean_list(parsed.get("accords")),
        "notes": {
            "top": _clean_list(notes.get("top")),
            "heart": _clean_list(notes.get("heart")),
            "base": _clean_list(notes.get("base")),
        },
        "inspired_by": parsed.get("inspired_by") or None,
        "summary": str(parsed.get("summary") or ""),
    }
    # "found" with nothing to show is not found.
    has_content = result["accords"] or any(result["notes"].values())
    if not has_content:
        result["found"] = False
    return result


def _extract_sources(response) -> list[dict]:
    sources, seen = [], set()
    try:
        chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
    except (AttributeError, IndexError, TypeError):
        return sources
    for chunk in chunks:
        web = getattr(chunk, "web", None)
        uri = getattr(web, "uri", None)
        if not uri or uri in seen:
            continue
        seen.add(uri)
        sources.append({"title": getattr(web, "title", None) or uri, "url": uri})
    return sources


def lookup_details(brand: str, name: str) -> dict:
    """Web-grounded notes for a fragrance that is not in our dataset (unverified)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Export it before starting the backend, "
            "e.g. export GEMINI_API_KEY=your_key_here"
        )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=_LOOKUP_PROMPT.format(brand=brand, name=name),
        # Search grounding can't be combined with forced-JSON output, so the JSON
        # shape is requested in the prompt and parsed defensively above.
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
    )

    result = _normalize_lookup(_parse_json_object(response.text), brand, name)
    result["sources"] = _extract_sources(response)
    return result

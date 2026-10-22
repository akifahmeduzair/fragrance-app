# Fragrance?

A grad-seminar prototype: scan or search a fragrance, see its notes and what
it's "inspired by," and get warned before buying something that smells like
what you already own.

## How it works (the pipeline)

1. **Identify** (image → name): a photo goes to the Gemini API, which is
   good at reading labels/bottle shapes. Gemini is asked ONLY for a brand +
   name guess — never for notes or facts.
2. **Ground** (name → facts): that guess is fuzzy-matched against our own
   fixed dataset (`backend/data/fragrances.json`) so all displayed notes,
   accords, and dupe relationships come from a source we control, not from
   an LLM's memory. This avoids hallucinated fragrance facts.
3. **Compare** (similarity engine): each fragrance is vectorized from its
   accords + notes (TF-IDF, classical baseline) and compared with cosine
   similarity. This powers both the "closest matches" list and the
   duplicate-purchase warning against your own collection.

This split is the main design decision worth explaining in your writeup:
multimodal AI is used where it's strong (reading a label from a photo),
and a grounded dataset + classical similarity is used where LLMs are weak
(recalling exact facts).

## Project structure

```
fragrance-app/
  backend/           FastAPI server
    main.py          API routes
    services/
      gemini_service.py   Step 1: image -> brand/name guess
      similarity.py       Step 3: TF-IDF + cosine similarity engine
    data/
      fragrances.json     ~20 curated demo fragrances (notes, accords, dupes)
  frontend/          React (Vite) app
    src/
      components/    SearchPanel, ScanPanel, InventoryPanel, FragranceDetail, NotesPyramid
      api.js         fetch wrapper for the backend
```

## Running it

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here   # get one free at aistudio.google.com
uvicorn main:app --reload --port 8000
```

The app still works without a Gemini key for search/inventory/similarity —
only the "Scan a bottle" tab needs it.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (usually `http://localhost:5173`). If your
backend runs somewhere other than `http://localhost:8000`, create a
`.env` file in `frontend/` with:

```
VITE_API_URL=http://your-backend-url
```

## Extending it for the full seminar writeup

- **Bigger dataset:** the ~20-fragrance sample in `fragrances.json` is
  enough to demo the pipeline. For real coverage, swap in a larger
  Fragrantica-derived dataset (several exist on Kaggle for research use) —
  just match the same JSON shape.
- **Classical vs. embeddings comparison:** `services/similarity.py` is
  intentionally the classical (TF-IDF) baseline. Swapping in a sentence-
  embedding model and comparing accuracy against known real-world dupes
  (several are already seeded in the dataset, e.g. Sauvage ↔ Fresh Blvd.)
  is a natural mini-evaluation for your paper.
- **Persistence:** inventory is currently a flat JSON file
  (`backend/data/inventory.json`) for simplicity — fine for a single-user
  demo, swap for SQLite/Postgres if you want multi-user support.

# Backend (FastAPI)

## Quick start
```bash
# 1) Create venv
python -m venv .venv
# 2) Activate (Windows PowerShell)
. .venv/Scripts/Activate.ps1
# 3) Install deps
pip install -r requirements.txt
# 4) Run dev server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
#    (or) python main.py
```

## Endpoints
- POST `/api/analyze` → Analyze code and return score, issues, metrics
- POST `/api/report` → Return a simple text report for download
- GET `/api/health` → Health check

## Notes
- CORS is enabled for `http://localhost:5173` and `http://localhost:8080` (Vite defaults).

## Optional: External AI keys
- `GOOGLE_API_KEY`: enables Gemini fixes (`GOOGLE_MODEL` defaults to `gemini-1.5-flash`).
- `OPENROUTER_API_KEY`: enables OpenRouter fixes (`OPENROUTER_MODEL` defaults to `google/gemini-2.0-flash-exp:free`).
- Without these keys, the backend performs local heuristic fixes only.
- Check configuration via `GET /api/status`.

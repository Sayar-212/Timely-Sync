# Automated Timetable Backend (Multi-Agent + CSP Hybrid)

Backend-only Python project that generates class timetables using a **multi-agent** architecture and **Google OR-Tools CP-SAT** as the single source of truth for hard constraints. Gemini API is used for NL parsing & semantic checks (offline fallback included).

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r timetable_backend/requirements.txt
export GEMINI_API_KEY=YOUR_KEY   # optional
python timetable_backend/main.py
```
Outputs appear in `outputs/` (JSON + PDF).

## Tests
```bash
pytest -q
```

## Config
See `config/settings.py` for environment variables.

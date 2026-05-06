# AMP Eingabemaske

A small report catalog app with a static frontend and a lightweight local Python backend.

## Current setup

Frontend:
- `index.html`
- `styles.css`
- `app.js`
- `assets/`

Backend:
- `server.py`
- JSON API on the same origin
- file persistence in `data/reports.json`
- SQLite persistence in `data/reports.sqlite3`

## Features

- guided report entry flow
- live summary in the UI
- markdown export
- saved reports list
- local JSON API
- dual persistence: JSON file and SQLite
- light and dark mode toggle
- mobile-oriented header and action layout work in progress

## Run locally

Requirements:
- Python 3.9+
- a modern browser

Start the app:

```bash
cd /Users/nb-j2v5jx79py/Desktop/Repos/AMP_Eingabemaske
python3 server.py
```

Then open:

- `http://127.0.0.1:8000/`

Health check:

- `http://127.0.0.1:8000/api/health`

## API

### `GET /api/health`
Returns a simple health response.

Example response:

```json
{ "ok": true }
```

### `GET /api/reports`
Returns all saved report entries.

Example response:

```json
{
  "entries": []
}
```

### `POST /api/reports`
Creates one report entry.

Required payload fields:
- `signature`
- `exportMarkdown`

Typical payload:

```json
{
  "signature": "unique-signature",
  "name": "Sales Dashboard",
  "fachabteilung": "Vertrieb",
  "timestamp": "07.05.2026, 12:00:00",
  "exportMarkdown": "# Berichtskatalog-Eintrag",
  "summary": {
    "berichtsname": "Sales Dashboard"
  }
}
```

### `DELETE /api/reports/:id`
Deletes a saved report by id.

## Persistence model

The backend writes each saved entry into:
- SQLite database: `data/reports.sqlite3`
- JSON mirror file: `data/reports.json`

SQLite is the main structured store.
The JSON file is a readable mirror and fallback handoff format.

## Frontend behavior

- report save/load/delete now uses the backend API
- theme stays in browser storage
- if the app is opened with `file://`, the frontend tries `http://127.0.0.1:8000/api`
- preferred usage is still to open the app through the local server, not via `file://`

## Important files

- `app.js`: questionnaire flow, summary rendering, API calls
- `server.py`: static file server, API routes, JSON and SQLite storage
- `styles.css`: layout, header, mobile behavior
- `index.html`: app shell and header markup

## Verification already done

Checked in the previous implementation session:
- `node --check app.js`
- `python3 -m py_compile server.py`
- direct store roundtrip in Python: create, list, delete
- JSON and SQLite file creation verified

## Known open points

These points should be checked in a real local browser session:
- mobile header layout on small widths
- mobile action layout robustness
- theme hydration and storage edge cases
- full localhost smoke test of UI + API together

## Git notes

Runtime data is ignored by Git:
- `data/`
- `__pycache__/`

## Next recommended steps

1. Run the app on `http://127.0.0.1:8000/`
2. Test save, load and delete in the browser
3. Review mobile layout again on a narrow viewport
4. Decide whether the backend should stay local-only or be prepared for deployment

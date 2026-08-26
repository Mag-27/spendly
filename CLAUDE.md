# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a personal expense tracker built with Flask, developed incrementally as a series of numbered steps (see the "Step N" comments in `app.py`). Step 1 (database setup) is implemented — `database/db.py` is a working SQLite layer, not a stub. Much of the rest of the backend is still intentionally unimplemented scaffolding — routes exist but return placeholder strings. When asked to "implement" one of these remaining steps, check the placeholder route first; its comment and stub body describe the expected shape of the solution (route signature, step number) before you design your own.

## Commands

Setup:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the app (serves on port 5001):
```bash
python app.py
```

Run tests (pytest + pytest-flask are in requirements.txt, but no test files exist yet — create them under a `tests/` directory):
```bash
pytest
pytest tests/test_file.py::test_name   # run a single test
```

There is no lint/format tooling configured in this repo.

## Architecture

- **`app.py`** — single Flask application module; all routes are defined directly on `app` (no blueprints). `debug=True`, port `5001`.
- **`database/db.py`** — owns all SQLite access via three functions. `get_db()` opens a fresh `sqlite3.connect()` per call, sets `row_factory = sqlite3.Row`, and runs `PRAGMA foreign_keys = ON` (set per-connection — SQLite doesn't persist this in the file, so any code opening a connection directly instead of via `get_db()` would silently lose FK enforcement). `init_db()` creates the `users` and `expenses` tables (`CREATE TABLE IF NOT EXISTS`; `expenses.user_id` is a foreign key to `users.id`). `seed_db()` is idempotent (checks the `users` row count first) and inserts one demo user (`demo@spendly.com` / `demo123`, hashed via `werkzeug.security.generate_password_hash`) plus 8 sample expenses spanning the 7 fixed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other). `app.py` calls `init_db()` and `seed_db()` inside `app.app_context()` at module load, before any route is defined. The SQLite file is `expense_tracker.db` (gitignored, created at runtime — no schema is committed).
- **`templates/`** — Jinja2 templates. `base.html` is the shared layout (navbar, footer, `{% block content %}`); `landing.html`, `register.html`, `login.html` extend it. Auth forms POST to `/register` and `/login` and render an `error` variable in a `.auth-error` block on failure.
- **`static/css/style.css`** — all styling lives in this one file, organized by section (variables → reset → navbar → hero → buttons → auth → footer → responsive). Uses CSS custom properties defined in `:root` for the color/type/spacing system (e.g. `--ink`, `--accent`, `--paper`, `--font-display`, `--font-body`). Reuse these variables rather than hardcoding new colors.
- **`static/js/main.js`** — currently empty; add client-side behavior here as features require it.

## Current state / what's left

The database layer (Step 1) is done. Routes in `app.py` marked "Placeholder routes — students will implement these" still return plain strings, not templates: `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. There is no session/auth handling and no expense model/business logic yet — these all need to be built on top of the `database/db.py` functions described above.

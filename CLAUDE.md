# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a personal expense tracker built with Flask, developed incrementally as a series of numbered steps (see the "Step N" comments in `app.py` and `database/db.py`). Much of the backend is intentionally unimplemented scaffolding — routes exist but return placeholder strings, and `database/db.py` is a stub describing what to build rather than working code. When asked to "implement" a feature, check these placeholders first; they describe the expected shape of the solution (function names, responsibilities) before you design your own.

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
- **`database/db.py`** — intended to own all SQLite access via three functions: `get_db()` (connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), `seed_db()` (inserts sample dev data). The SQLite file is `expense_tracker.db` (gitignored, created at runtime — no schema is committed).
- **`templates/`** — Jinja2 templates. `base.html` is the shared layout (navbar, footer, `{% block content %}`); `landing.html`, `register.html`, `login.html` extend it. Auth forms POST to `/register` and `/login` and render an `error` variable in a `.auth-error` block on failure.
- **`static/css/style.css`** — all styling lives in this one file, organized by section (variables → reset → navbar → hero → buttons → auth → footer → responsive). Uses CSS custom properties defined in `:root` for the color/type/spacing system (e.g. `--ink`, `--accent`, `--paper`, `--font-display`, `--font-body`). Reuse these variables rather than hardcoding new colors.
- **`static/js/main.js`** — currently empty; add client-side behavior here as features require it.

## Current state / what's left

Routes in `app.py` marked "Placeholder routes — students will implement these" return plain strings, not templates: `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. There is no session/auth handling, no ORM, and no expense model yet — these all need to be built on top of the `database/db.py` scaffolding described above.

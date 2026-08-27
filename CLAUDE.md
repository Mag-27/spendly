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
- **`templates/`** — Jinja2 templates. `base.html` is the shared layout (navbar, footer, `{% block content %}`); `landing.html`, `register.html`, `login.html`, `profile.html` extend it. Auth forms POST to `/register` and `/login` and render an `error` variable in a `.auth-error` block on failure.
- **`static/css/style.css`** — all styling lives in this one file, organized by section (variables → reset → navbar → hero → buttons → auth → profile → footer → responsive). Uses CSS custom properties defined in `:root` for the color/type/spacing system (e.g. `--ink`, `--accent`, `--paper`, `--font-display`, `--font-body`). Reuse these variables rather than hardcoding new colors. Categorized data uses the `--cat-<category>` / `--cat-<category>-bg` token pairs with the matching `.cat-badge--<category>` and `.cat-bar--<category>` classes — one pair per fixed category.
- **`static/js/main.js`** — currently empty; add client-side behavior here as features require it.

## Current state / what's left

The database layer (Step 1), registration (Step 2), login/logout (Step 3), and the profile page (Step 4) are done. Routes in `app.py` marked "Placeholder routes — students will implement these" still return plain strings, not templates: `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. There is no expense model/business logic yet — that needs to be built on top of the `database/db.py` functions described above.

`/profile` (Step 4) was built UI-first: the full layout — identity card, three-card summary row, transaction table, category breakdown — renders from the `_PROFILE_*` constants at the top of `app.py`, **not** from the database. Nothing on that page is real yet. Step 5 replaces those four constants with queries and adds the `get_user_by_id()` helper `database/db.py` still lacks. The route guards itself inline with `if not session.get("user_id"): return redirect(url_for("login"))` — there is still no shared `@login_required` decorator.

Auth is complete: `/register` and `/login` both handle `GET` + `POST`, and `/logout` is **`POST`-only** (a `GET` returns 405 — state-changing actions are kept off `GET` so a stray link prefetch can't sign a user out). `session["user_id"]` is the single canonical "who is signed in" key; `/login` calls `session.clear()` before establishing it (session-fixation defence — `/register` does not, since it creates a brand-new account), and `/logout` clears it. Failed logins render one generic `_LOGIN_ERROR` for both unknown emails and wrong passwords, and always run `check_password_hash` — against `_DUMMY_PASSWORD_HASH` when no user matched — so neither the message nor the response time reveals whether an account exists. Emails are normalized with `.strip().lower()` in both handlers; the two must stay in sync or existing accounts become unreachable.

The navbar in `base.html` branches on `session.get('user_id')`: signed out it shows "Sign in" + "Get started", signed in it shows a `.nav-user` name span + a `POST` "Log out" form-button + a "Profile" link. The name comes from `current_user_name`, which only `/profile` passes; every other page falls back via `| default('Account')`, so that filter is load-bearing — dropping it breaks `/`, `/login`, and `/register` for signed-in visitors. Step 5 should replace it with a context processor. Profile carries `.nav-cta` deliberately — `static/css/style.css` hides `.nav-links a:not(.nav-cta)` at ≤600px, so the pill class is what keeps it visible on mobile.

Still missing: there is no shared `@login_required` decorator (only `/profile` guards itself, inline), `/login` has no `?next=` redirect, and the project has no CSRF protection — all deferred to later steps.

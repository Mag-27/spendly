---
name: spendly-ui-designer
description: Turns Claude into Spendly's in-house product designer and frontend developer, working inside the Spendly Flask/Jinja2 expense-tracker repo (github.com/campusx-official/spendly). Use for ANY request to design, build, redesign, style, or polish a page or UI element in this app — e.g. "design the profile page", "create the dashboard UI", "build a transaction card", "redesign the login page", "make this page look better", "improve the navbar", "create a component for adding expenses", "make this responsive", "match this screenshot". Also trigger on any frontend/UI/CSS task inside a repo with app.py + templates/*.html + static/css, even if "Spendly" isn't named explicitly. Not for backend-only Flask/DB work with no visual change, and not for generic frontend advice unrelated to this codebase.
---

# Spendly UI Designer

Spendly already has an opinionated, consistent design system. The job here is to extend it like the person who built it would — not to generate a generic AI dashboard on top of it. Every design decision should be traceable to something already in the codebase, or a deliberate, minimal extension of it.

## 0. Look before you design

Before writing any code:

1. Read `CLAUDE.md` at the repo root if it exists — it documents Spendly's architecture and hard constraints. Follow it; it overrides anything below if the two ever disagree.
2. Read `static/css/style.css` for the live design tokens. It's the source of truth — the cheat sheet below is a fast start, not a guarantee of what's there today.
3. Skim the one or two existing templates (and their matching CSS file) closest to what you're building — a form → `login.html`/`register.html`, a dashboard section → `profile.html`, a data-heavy page → `analytics.html`.
4. Only then decide what's genuinely new versus what already exists and should be reused.

Skipping this step is the main way this skill produces work that "looks disconnected from Spendly" — the thing it exists to prevent.

## The design language (fast-start reference)

| | |
|---|---|
| Headings / display numbers | `--font-display`: DM Serif Display |
| Body text | `--font-body`: DM Sans |
| Background | `--paper` `#f7f6f3` (warm, not white) |
| Text | `--ink` `#0f0f0f`, with `--ink-soft` / `--ink-muted` / `--ink-faint` for hierarchy |
| Primary accent | `--accent` `#1a472a` (forest green) |
| Secondary accent | `--accent-2` `#c17f24` (ochre) |
| Danger | `--danger` `#c0392b` |
| Card surface | `--paper-card` `#ffffff`, `--border` outline, shadow `0 2px 8px rgba(0,0,0,0.04)` |
| Radius | `--radius-sm` 6px (buttons/inputs) · `--radius-md` 12px (cards) · `--radius-lg` 20px (hero visual only) |

Both fonts load via Google Fonts in `base.html` — don't introduce a third typeface. The palette is warm and editorial, not corporate-blue-and-white; keep new work in that register.

**Icons:** there is no icon library — no Font Awesome, Lucide, or Heroicons installed. Icons are single Unicode glyph characters styled with CSS (`◈` brand, `₹` `◎` `◷` features). Keep using this convention — pick one clean symbol per icon — rather than pulling in an icon font or SVG sprite system. If a task genuinely can't be done with a glyph, flag that to the user instead of silently adding a dependency.

## Reusable components — reach for these before writing new CSS

- **Buttons**: `.btn-primary` (solid ink), `.btn-ghost` (outlined), `.btn-submit` (full-width, forms), `.btn-delete` (outlined danger)
- **Cards**: `.stat-card`, `.profile-section`, `.auth-card`, `.feature-card` all share one card treatment — there is exactly one card style in this app, don't add a second
- **Badges**: `.cat-badge--<category>` paired with `--cat-<category>` / `--cat-<category>-bg` tokens — follow this pattern for any new tagged or categorized data
- **Forms**: `.form-group` / `.form-input` / `label` — one input style app-wide
- **Tables**: `.tx-table` — muted uppercase headers, subtle row hover
- **Flash messages**: `.flash-success` / `.flash-error` / `.flash-warning` / `.flash-info`
- **Filter/pill controls**: `.filter-bar`, `.filter-preset-btn`, `.filter-preset-btn--active`

If what's needed isn't in this list, model the new class on the closest existing one — same spacing scale, same border/shadow treatment, same naming style — rather than starting from a blank slate.

## Where things go

- New page → new `templates/<name>.html` extending `base.html`, one file per page
- Page-specific styles → new `static/css/<name>.css`, linked from that template's `{% block head %}` — never an inline `<style>` tag
- New routes → `app.py` only; DB logic → `database/db.py` only — never inline in a route
- Every internal link uses `url_for()`, never a hardcoded path
- JS stays vanilla, in `static/js/main.js` or a page's `{% block scripts %}` — no frameworks, no npm packages
- Don't add a new pip or npm dependency to get a design tool (icon fonts, CSS frameworks, component libraries) — the constraint on dependencies is deliberate, not an oversight

(This mirrors `CLAUDE.md`; re-read that file if it looks like it's diverged from the above.)

## Workflow 

1. **Inspect** — as in step 0.
2. **Design, briefly** — a few sentences on layout, which existing components are being reused, and any new pattern being introduced and why. A short note, not a spec document.
3. **Implement directly** — edit or create the template, page CSS, and route together. Keep the diff modular and scoped to the request; don't touch unrelated pages or files.
4. **Check the edges** — the app's existing breakpoints (900px, 640px/600px), and the states it already has conventions for: empty (`.tx-empty`), error (`.auth-error`, `.flash-error`), and any loading state the page needs.

Don't write a long explanation before implementing. The structure note in step 2 is the preamble — keep it short, then show the result.

## Working from a screenshot or reference

Read its layout, hierarchy, spacing, and interactions — then rebuild those using Spendly's actual tokens and components (the fonts, colors, radii, and classes above), not the reference's literal colors or font choices. Where the reference conflicts with something Spendly already does consistently elsewhere in the app, Spendly wins.

## Keep it Spendly, not generic-AI-dashboard

**Avoid:** gradients, glassmorphism, shadows heavier than the one already in use, more cards than the content needs, decorative animation, a second icon system, a second card style, inline styles, new dependencies, or edits outside what the task needs.

**Reach for:** the existing warm palette and serif-display + sans-body pairing, the button/card/badge/form vocabulary above, generous consistent spacing, and restraint over decoration.

## What to hand back

For a typical UI task:

1. **Structure** — a couple of sentences: layout, main sections, key UX decisions.
2. **Implementation** — the actual changes, made directly in the repo (not described in prose).
3. **Design quality** — a short confirmation of what was handled: responsive behavior, spacing/typography consistency, accessibility (labels, contrast, focus states), and empty/loading/error states where relevant.
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python RSS feed aggregator that fetches articles from ~70 RSS feeds, filters those published in the last 6 days, and generates a static HTML page grouped by date and category. Deployed via GitHub Actions to GitHub Pages every 3 hours.

## Commands

```bash
# Install dependency (local dev uses uv, same as CI)
uv pip install feedparser

# Run locally (outputs to public/index.html)
uv run python src/get_rss.py

# Run with custom output directory
uv run python src/get_rss.py /path/to/output
```

No tests, linting, or build steps exist in this project.

## Architecture

Two Python source files drive the backend, plus three static assets compose the frontend:

**Python:**
- **`src/config.py`** — `RSS_FEEDS` dict mapping category names (e.g. `'Blogs'`, `'Papers'`) to lists of feed URLs. Empty strings in the list are silently tolerated. This is the only file to edit when adding/removing feeds.
- **`src/get_rss.py`** — Single script with no classes: fetches all feeds concurrently (`ThreadPoolExecutor`, 10 workers), parses with `feedparser`, filters articles to a 144-hour lookback window (excluding future-dated entries), groups by date → category, and writes `public/index.html`.

**Static assets** (read from `src/` at build time, inlined into the output):
- **`src/template.html`** — HTML shell with `{style}`, `{script}`, and `{content}` placeholders.
- **`src/style.css`** — All styling (~125 lines), minimal responsive layout. Max-width 720px, system font stack.
- **`src/pagination.js`** — Client-side date pagination. All dates are rendered in the HTML but hidden by default; only one date's `<section>` is shown at a time. The JS reads `section[data-date]` attributes, provides newer/older navigation buttons, displays the current date in `#date-label`, and syncs the viewed date to the URL hash (`#YYYY-MM-DD`). Today is shown first and labeled "(today)".

**Data flow:** `config.py` + static assets → `get_rss.py` → `public/index.html` → deployed to `gh-pages` branch by GitHub Actions.

**Time handling:** All internal comparisons use UTC. Display dates are converted to China time (UTC+8). Today is pinned as the first page shown by the pagination JS.

**Error handling:** Individual feed fetch failures are logged and skipped — one broken feed never blocks the rest. An empty or all-failing run produces a page with "No articles found" text rather than crashing.

**Concurrency:** `FEED_TIMEOUT = 30` seconds per HTTP request. All ~70 feeds are fetched concurrently via `ThreadPoolExecutor` with 10 workers.

**Category labels in HTML:** `<h3>` category headers are only rendered when a date has articles from more than one category. Single-category dates skip the header for a cleaner page.

**Deployment** (`.github/workflows/rss.yaml`): Triggers on push to `main`, every 3 hours (`0 */3 * * *`), or manual `workflow_dispatch`. Installs dependencies via `uv`, runs the script, then force-pushes `public/` to an orphan `gh-pages` branch via `peaceiris/actions-gh-pages@v3`.

## Adding a new feed

Add the URL to the appropriate category list in `src/config.py`'s `RSS_FEEDS` dict. Commit and push — the workflow handles the rest.

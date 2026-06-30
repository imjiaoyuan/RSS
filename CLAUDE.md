# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python RSS feed aggregator that fetches articles from ~90 RSS feeds plus custom scrapers, filters those published in the last 6 days (144 hours), and generates a static HTML page grouped by date and category. Deployed via GitHub Actions to GitHub Pages every 3 hours.

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

The backend has two kinds of content sources — standard RSS feeds and custom route scrapers — plus three static assets compose the frontend:

**Python backend:**
- **`src/config.py`** — `RSS_FEEDS` dict mapping category names (e.g. `'Blogs'`, `'News'`) to lists of feed URLs and/or route names. Empty strings in the list are silently tolerated. Feed URLs starting with `http://` or `https://` are fetched as RSS; bare names like `"sspai_matrix"` are resolved through the routes system. This is the only file to edit when adding/removing feeds.
- **`src/get_rss.py`** — Single script with no classes: fetches all feeds concurrently (`ThreadPoolExecutor`, 10 workers), retries failed HTTP requests 3× with exponential backoff (`2^attempt` seconds), uses a permissive SSL context (no certificate verification), parses RSS with `feedparser`, sorts entries by publish date descending, filters articles to a 144-hour lookback window (excluding future-dated entries), groups by date → category, and writes `public/index.html`.
- **`src/routes/`** — Custom scraper package. `__init__.py` exports `load_routes()`, which auto-discovers all `*.py` files in the directory (excluding `_`-prefixed), imports them, and registers any module that exposes both `ROUTE_CONFIG` (a dict) and a `fetch(config) -> list[dict]` function. Each route module (e.g. `sspai_matrix.py`) is a self-contained scraper: it fetches an HTML page, parses article metadata with regex, applies the same 144h filter, and returns article dicts compatible with the standard feed pipeline.

**Static assets** (read from `src/` at build time, inlined into the output):
- **`src/template.html`** — HTML shell with `{style}`, `{script}`, and `{content}` placeholders.
- **`src/style.css`** — All styling (~125 lines), minimal responsive layout. Max-width 720px, system font stack.
- **`src/pagination.js`** — Client-side date pagination. All dates are rendered in the HTML but hidden by default; only one date's `<section>` is shown at a time. The JS reads `section[data-date]` attributes, provides newer/older navigation buttons, displays the current date in `#date-label`, and syncs the viewed date to the URL hash (`#YYYY-MM-DD`). Today is shown first and labeled "(today)".

**Data flow:** `config.py` + static assets → `get_rss.py` → `public/index.html` → deployed to `gh-pages` branch by GitHub Actions.

**Time handling:** All internal comparisons use UTC. Display dates are converted to China time (UTC+8). Today is pinned as the first page shown by the pagination JS.

**Error handling:** Individual feed fetch failures are logged and skipped — one broken feed never blocks the rest. An empty or all-failing run produces a page with "No articles found" text rather than crashing.

**Concurrency:** `FEED_TIMEOUT = 30` seconds per HTTP request. All feeds are fetched concurrently via `ThreadPoolExecutor` with 10 workers. Route scrapers run sequentially after all RSS feeds complete.


**Deployment** (`.github/workflows/rss.yaml`): Triggers on push to `main`, every 3 hours (`0 */3 * * *`), or manual `workflow_dispatch`. Installs dependencies via `uv`, runs the script, then force-pushes `public/` to an orphan `gh-pages` branch via `peaceiris/actions-gh-pages@v3`.

## Adding a new feed

**Standard RSS feed:** Add the URL to the appropriate category list in `src/config.py`'s `RSS_FEEDS` dict. Commit and push — the workflow handles the rest.

**Custom scraper (for sites without RSS):**
1. Create a new `.py` file in `src/routes/` (e.g. `example_scraper.py`).
2. Define `ROUTE_CONFIG` (dict with at least `"url"`) and a `fetch(config) -> list[dict]` function that returns article dicts with keys: `title`, `link`, `published_dt` (UTC-aware datetime), `date_str` (`"YYYY-MM-DD"` in China time), `time_str` (`"HH:MM"` in China time).
3. Apply the 144-hour filter (`cutoff = now - timedelta(hours=144)`) inside `fetch` — the main pipeline does NOT re-filter route results.
4. Add the module's filename stem (e.g. `"example_scraper"`) to the desired category in `RSS_FEEDS`.

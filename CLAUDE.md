# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python RSS feed aggregator that fetches articles from ~95 RSS feeds across three categories (Blogs, News, Publications), filters those published in the last 6 days (144 hours), and generates a static HTML page grouped by date and category. Deployed via GitHub Actions to GitHub Pages every 3 hours.

## Commands

```bash
# Install dependency (into existing .venv)
uv pip install feedparser

# Run locally (outputs to public/index.html)
uv run python src/get_rss.py

# Run with custom output directory
uv run python src/get_rss.py /path/to/output
```

No tests, linting, or build steps exist in this project.

## Architecture

**Python backend:**
- **`src/config.py`** — `RSS_FEEDS` dict mapping category names (`'Blogs'`, `'News'`, `'Publications'`) to lists of feed URLs. Empty strings are silently tolerated. Feed URLs starting with `http://` or `https://` are fetched as RSS; bare names (e.g. `"example_scraper"`) would be resolved through the routes system. This is the only file to edit when adding/removing feeds.
- **`src/utils.py`** — Shared HTTP fetch with retry logic. Exports `fetch_url(url, timeout=30)` (returns `bytes`, retries 3× with exponential backoff `2^attempt` seconds), `FEED_TIMEOUT` (30s), `USER_AGENT`, and `MAX_RETRIES` (3). Creates a permissive SSL context (no certificate verification) at module level.
- **`src/get_rss.py`** — Single script with no classes. `get_latest_articles(feed_url)` fetches and parses one RSS feed with `feedparser`, sorts entries by `published_parsed` → `updated_parsed` descending, filters to 144h lookback (excluding future-dated entries), and returns article dicts with `category: None`. `main()` orchestrates everything: dispatches RSS feeds concurrently (`ThreadPoolExecutor`, 10 workers), then runs route scrapers sequentially, deduplicates by link (global `seen_links` set), assigns categories, groups by date → category, and calls `generate_html()`. Category assignment happens exclusively in `main()`, not in the fetcher.
- **`src/routes/`** — Custom scraper package. `__init__.py` exports `load_routes()`, which auto-discovers all `*.py` files in the directory (excluding `_`-prefixed), imports them, and registers any module that exposes both `ROUTE_CONFIG` (a dict with at least `"url"`) and a `fetch(config) -> list[dict]` function. Currently no active route scrapers — the directory is empty aside from `__init__.py`. Route scrapers, when present, are runnable standalone for debugging.

**Static assets** (read from `src/` via `SCRIPT_DIR` at build time, inlined into the output):
- **`src/template.html`** — HTML shell with `{style}`, `{script}`, and `{content}` placeholders.
- **`src/style.css`** — All styling (~125 lines), minimal responsive layout. Max-width 720px, system font stack. Uses `content-visibility: auto` + `contain-intrinsic-size` on `<li>` elements for rendering performance on long article lists.
- **`src/pagination.js`** — Client-side date pagination. All dates are rendered in the HTML but hidden by default; only one date's `<section>` is shown at a time. The JS reads `section[data-date]` attributes, provides newer/older navigation buttons, displays the current date in `#date-label`, and syncs the viewed date to the URL hash (`#YYYY-MM-DD`). Today is shown first and labeled "(today)". If no articles were published today, an empty "No articles published today." section is still inserted as the first page.

**Data flow:** `config.py` + `utils.py` + static assets → `get_rss.py` → `public/index.html` → deployed to `gh-pages` branch by GitHub Actions (force-pushed as an orphan branch, so `gh-pages` has no commit history).

**Time handling:** All internal comparisons use UTC. Display dates are converted to China time (UTC+8). Today is pinned as the first page shown by the pagination JS.

**Error handling:** Individual feed fetch failures are logged and skipped — one broken feed never blocks the rest. An empty or all-failing run produces a page with "No articles found" text rather than crashing.

**Concurrency:** `FEED_TIMEOUT = 30` seconds per HTTP request. RSS feeds are fetched concurrently via `ThreadPoolExecutor` with 10 workers. Route scrapers run sequentially after all RSS feeds complete.

**Deduplication:** Articles are deduplicated by link across all feeds and routes via a single `seen_links` set in `main()`. If two feeds produce the same URL, only the first processed wins.

**Deployment** (`.github/workflows/rss.yaml`): Triggers on push to `main`, every 3 hours (`0 */3 * * *`), or manual `workflow_dispatch`. Installs dependencies via `uv`, runs the script, then force-pushes `public/` to an orphan `gh-pages` branch via `peaceiris/actions-gh-pages@v3`.

## Adding a new feed

**Standard RSS feed:** Add the URL to the appropriate category list in `src/config.py`'s `RSS_FEEDS` dict. Commit and push — the workflow handles the rest.

**Custom scraper (for sites without RSS):**
1. Create a new `.py` file in `src/routes/` (e.g. `example_scraper.py`).
2. Import `fetch_url` from `utils` (use it to fetch HTML or RSS; it handles retries, SSL, and user-agent). If the scraper consumes RSS from a bridge API, also import `feedparser`.
3. Define `ROUTE_CONFIG` (dict with at least `"url"`) and a `fetch(config) -> list[dict]` function that returns article dicts with keys: `title`, `link`, `published_dt` (UTC-aware datetime), `date_str` (`"YYYY-MM-DD"` in China time), `time_str` (`"HH:MM"` in China time). Do NOT include a `category` key — the main pipeline assigns it.
4. Apply the 144-hour filter (`cutoff = datetime.now(timezone.utc) - timedelta(hours=144)`) inside `fetch` — the main pipeline does NOT re-filter route results.
5. Add the module's filename stem (e.g. `"example_scraper"`) to the desired category in `RSS_FEEDS`.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python RSS feed aggregator — fetches ~95 feeds across three categories (Blogs, News, Publications), filters to last 6 days, generates a static HTML page grouped by date and category. Deployed via GitHub Actions to GitHub Pages every 3 hours.

## Commands

```bash
uv venv --python 3.11                 # first time only
uv pip install feedparser             # install dependency (local venv)
uv run python src/get_rss.py          # output to public/index.html
uv run python src/get_rss.py ./public # explicit output dir
```

CI uses `uv pip install --system feedparser` (no venv). No tests, linting, or build steps.

## Architecture

- **`src/config.py`** — `RSS_FEEDS` dict: category → list of feed URLs. Only file to edit when adding/removing feeds.
- **`src/utils.py`** — `fetch_url(url)` with retry (3×, exponential backoff), permissive SSL (no cert verification).
- **`src/get_rss.py`** — Main script. Fetches RSS feeds concurrently (`ThreadPoolExecutor`, 10 workers), then runs custom route scrapers sequentially, deduplicates by link, assigns categories, generates HTML. Category is assigned in `main()`, not in the fetcher.
- **`src/routes/`** — Custom scraper directory. Drop a `.py` file with `ROUTE_CONFIG` dict (must have `"url"` key) + `fetch(config) -> list[dict]`; it's auto-discovered by `__init__.py`. Add the filename stem to `RSS_FEEDS` to activate. RSS feeds are fetched concurrently but custom routes run sequentially after. Currently no custom scrapers are defined.
- **Time filtering** — `get_latest_articles()` handles the 144h cutoff for RSS feeds. Custom route scrapers and their `fetch()` must apply their own 144h filter internally — they return pre-filtered results.
- **Static assets** — `template.html`, `style.css`, `pagination.js` are inlined into the output. Pagination is client-side JS, today shown first.
- **Deployment** — `.github/workflows/rss.yaml`: triggers on push, every 3h, or manual. Force-pushes `public/` as orphan `gh-pages` branch.

Time: internal comparisons in UTC, display in UTC+8. Future-dated entries are dropped. Feeds that fail are logged and skipped — one failure never blocks the rest. **The script is silent on success** — log output only appears for errors, so no output means everything worked.

## Adding a feed

**RSS:** Add URL to `RSS_FEEDS` in `src/config.py`.

**Custom scraper:** Create `src/routes/<name>.py` with `ROUTE_CONFIG` (dict with `"url"`) and `fetch(config) -> list[dict]` (returning `title`, `link`, `published_dt`, `date_str`, `time_str`; no `category`). Apply 144h filter inside `fetch`. Add the module name to `RSS_FEEDS`.

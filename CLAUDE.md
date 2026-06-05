# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python RSS feed aggregator that fetches articles from ~70 RSS feeds, filters those published in the last 6 days, and generates a static HTML page grouped by date and category. Deployed via GitHub Actions to GitHub Pages every 3 hours.

## Commands

```bash
# Install dependency
pip install feedparser

# Run locally (outputs to public/index.html)
python src/get_rss.py

# Run with custom output directory
python src/get_rss.py /path/to/output
```

No tests, linting, or build steps exist in this project.

## Architecture

Two source files drive everything:

- **`src/config.py`** — `RSS_FEEDS` dict mapping category names (e.g. `'Blogs'`, `'Papers'`) to lists of feed URLs. Empty strings in the list are silently tolerated. This is the only file to edit when adding/removing feeds.
- **`src/get_rss.py`** — Single script with no classes: fetches all feeds concurrently (`ThreadPoolExecutor`, 10 workers), parses with `feedparser`, filters articles to a 144-hour lookback window (excluding future-dated entries), groups by date → category, and writes `index.html` from an inline `HTML_TEMPLATE` string. Accepts an optional output directory as `sys.argv[1]` (defaults to `public/`).

**Data flow:** `config.py` → `get_rss.py` → `public/index.html` → deployed to `gh-pages` branch by GitHub Actions.

**Time handling:** All internal comparisons use UTC. Display dates are converted to China time (UTC+8). Today's articles get a "(today)" label and are pinned to the top of the page.

**Error handling:** Individual feed fetch failures are logged and skipped — one broken feed never blocks the rest. An empty or all-failing run produces a page with "No articles found" text rather than crashing.

**Deployment** (`.github/workflows/rss.yaml`): Triggers on push to `main`, every 3 hours (`0 */3 * * *`), or manual `workflow_dispatch`. Uses `astral-sh/setup-uv` to install dependencies, runs the script, then force-pushes `public/` to an orphan `gh-pages` branch via `peaceiris/actions-gh-pages@v3`.

## Adding a new feed

Add the URL to the appropriate category list in `src/config.py`'s `RSS_FEEDS` dict. Commit and push — the workflow handles the rest.

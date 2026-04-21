# Copilot Instructions for Feeds Repository

## Project Overview

This is a Python-based RSS feed aggregator that collects articles from multiple RSS feeds published in the last 72 hours and generates a static HTML page. The project runs on GitHub Actions (scheduled daily + on push) and deploys the generated HTML to GitHub Pages.

**Key Components:**
- `src/config.py`: Centralized configuration defining the list of RSS feed URLs organized by category
- `src/get_rss.py`: Main script that fetches feeds, filters by date, and generates HTML output
- `.github/workflows/rss.yaml`: GitHub Actions workflow that runs the script and publishes to GitHub Pages

## Running the Script Locally

### Prerequisites
Install the `feedparser` dependency:
```bash
pip install feedparser
```

### Running the RSS Generator
Generate the HTML file in the `public/` directory (default):
```bash
python src/get_rss.py
```

Specify a custom output directory:
```bash
python src/get_rss.py /path/to/output
```

The script generates `index.html` with articles from the last 72 hours, grouped by date and sorted by time.

## Architecture

**Data Flow:**
1. `config.py` defines RSS feed URLs under the `RSS_FEEDS` dictionary, organized by category (Blogs, News, Papers, etc.)
2. `get_rss.py` fetches each feed using feedparser
3. Articles published in the last 72 hours are filtered and collected
4. Articles are grouped by category, then by date within each category, sorted by publication time, and rendered as HTML
5. `index.html` is written to the output directory with category sections as h2 headers and dates as h3 headers

**Error Handling:**
The script silently skips failed feeds (wrapped in try-except). This prevents one broken feed from blocking the entire job.

## Key Conventions

- **Feed Configuration**: RSS feed URLs are stored in `config.py` as a dictionary (`RSS_FEEDS`) with category keys. Add new feeds by appending to the appropriate list.
- **Time Zone**: All dates use UTC for consistency (datetime objects have `timezone.utc`)
- **Output**: The default output directory is `public/` - this matches GitHub Pages conventions and is already in `.gitignore`
- **Date Filtering**: The `time_delta_hours` parameter in `get_latest_articles()` controls how many hours back to look (default: 72 hours)
- **HTML Encoding**: Output uses UTF-8 encoding with `<meta charset="UTF-8">` to support international content

## Deployment

The GitHub Actions workflow (`.github/workflows/rss.yaml`) automatically:
- Runs on push to `main` branch
- Runs on schedule: daily at 22:30 UTC
- Can be triggered manually via `workflow_dispatch`
- Installs Python 3.11, feedparser, and runs the script
- Deploys output to the `gh-pages` branch using `peaceiris/actions-gh-pages@v3`
- Forces orphan branch to keep history clean

No manual deployment steps are needed.

## Common Modifications

**Adding a new RSS feed:**
1. Add the feed URL to the appropriate list in `config.py` under `RSS_FEEDS['Posts']` (or create a new category)
2. Commit and push - the workflow runs automatically

**Changing the time window:**
Modify the `time_delta_hours=72` parameter in the call to `get_latest_articles()` in `get_rss.py`

**Updating HTML template:**
Modify the `HTML_TEMPLATE` string in `get_rss.py` to change styling or structure

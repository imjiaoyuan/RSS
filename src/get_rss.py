import os
import sys
import ssl
import time
import html
import urllib.request
import feedparser
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import RSS_FEEDS
from routes import load_routes

FEED_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_RETRIES = 3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def _fetch_url(url, timeout=FEED_TIMEOUT):
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    raise last_err


def get_latest_articles(feed_url, time_delta_hours=144):
    latest_articles = []
    try:
        data = _fetch_url(feed_url)
        feed = feedparser.parse(data)
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(hours=time_delta_hours)
        china_tz = timezone(timedelta(hours=8))

        sorted_entries = sorted(
            feed.entries,
            key=lambda e: e.get('published_parsed') or e.get('updated_parsed') or (1, 1, 1, 0, 0, 0, 0, 1, 0),
            reverse=True
        )

        for entry in sorted_entries:
            published_time = entry.get('published_parsed') or entry.get('updated_parsed')
            if not published_time:
                continue
            published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)

            if not entry.title or not entry.title.strip():
                continue
            if published_dt > now:
                continue
            if published_dt >= time_threshold:
                china_dt = published_dt.astimezone(china_tz)
                latest_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published_dt': published_dt,
                    'date_str': china_dt.strftime('%Y-%m-%d'),
                    'time_str': china_dt.strftime('%H:%M'),
                    'category': None
                })
    except Exception as e:
        logging.error(f"Failed to fetch {feed_url}: {e}")
    return latest_articles


def render_articles(articles):
    parts = []
    for a in sorted(articles, key=lambda x: x['published_dt'], reverse=True):
        parts.append(
            f"<li><a href='{html.escape(a['link'])}'>{html.escape(a['title'])}</a>"
            f" <span>({a['time_str']})</span></li>"
        )
    return "\n".join(parts)


def generate_html(articles_by_date, output_path):
    china_tz = timezone(timedelta(hours=8))
    today_str = datetime.now(china_tz).strftime('%Y-%m-%d')

    sorted_dates = sorted(articles_by_date.keys(),
                          key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)

    if today_str in sorted_dates:
        sorted_dates.remove(today_str)
        sorted_dates.insert(0, today_str)
    elif sorted_dates:
        sorted_dates.insert(0, today_str)

    sections = []
    for date_str in sorted_dates:
        sections.append(f'<section data-date="{date_str}">')

        if date_str == today_str and date_str not in articles_by_date:
            sections.append("<p>No updates yet.</p>")
        else:
            by_cat = articles_by_date.get(date_str, {})
            cats = sorted(by_cat.keys())
            show_cat = len(cats) > 1

            for cat in cats:
                if show_cat:
                    sections.append(f"<h3>{cat}</h3>")
                sections.append("<ul>")
                sections.append(render_articles(by_cat[cat]))
                sections.append("</ul>")

        sections.append("</section>")

    full_content = "\n".join(sections) if sections else "<p>No articles found in the last 6 days.</p>"

    with open(os.path.join(SCRIPT_DIR, 'template.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    with open(os.path.join(SCRIPT_DIR, 'style.css'), 'r', encoding='utf-8') as f:
        style = f.read()
    with open(os.path.join(SCRIPT_DIR, 'pagination.js'), 'r', encoding='utf-8') as f:
        script = f.read()

    html_output = template.replace('{style}', style).replace('{script}', script).replace('{content}', full_content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)


def main():
    if len(sys.argv) < 2:
        output_dir = "public"
    else:
        output_dir = sys.argv[1]

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'index.html')

    articles_by_date = {}

    routes = load_routes()

    feed_tasks = []
    route_tasks = []
    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            if not feed_url.strip():
                continue
            if feed_url.startswith("http://") or feed_url.startswith("https://"):
                feed_tasks.append((category, feed_url))
            elif feed_url in routes:
                route_tasks.append((category, feed_url))
            else:
                logging.warning(f"Unknown feed or route: {feed_url}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_feed = {executor.submit(get_latest_articles, feed_url): (category, feed_url)
                          for category, feed_url in feed_tasks}

        for future in as_completed(future_to_feed):
            category, feed_url = future_to_feed[future]
            try:
                articles = future.result()
                for article in articles:
                    article['category'] = category
                    date_str = article['date_str']
                    if date_str not in articles_by_date:
                        articles_by_date[date_str] = {}
                    if category not in articles_by_date[date_str]:
                        articles_by_date[date_str][category] = []
                    articles_by_date[date_str][category].append(article)
            except Exception as e:
                logging.error(f"Error processing {feed_url}: {e}")

    for category, route_name in route_tasks:
        try:
            info = routes[route_name]
            articles = info["fetch"](info["config"])
            for article in articles:
                article['category'] = category
                date_str = article['date_str']
                if date_str not in articles_by_date:
                    articles_by_date[date_str] = {}
                if category not in articles_by_date[date_str]:
                    articles_by_date[date_str][category] = []
                articles_by_date[date_str][category].append(article)
            logging.info(f"Route '{route_name}': {len(articles)} articles")
        except Exception as e:
            logging.error(f"Route '{route_name}' failed: {e}")

    generate_html(articles_by_date, output_file)


if __name__ == '__main__':
    main()

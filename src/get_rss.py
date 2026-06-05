import os
import sys
import html
import urllib.request
import feedparser
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import RSS_FEEDS

FEED_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (compatible; RSS-Reader/1.0)'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; background: white; min-height: 100vh; }}
        h1 {{ font-size: 2em; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 2px solid #e0e0e0; }}
        h2 {{ font-size: 1.5em; margin: 30px 0 15px; color: #555; }}
        h3 {{ font-size: 1.2em; margin: 20px 0 10px; color: #666; }}
        ul {{ list-style: none; margin-bottom: 24px; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #f0f0f0; line-height: 1.8; }}
        li:last-child {{ border-bottom: none; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        span {{ color: #999; font-size: 0.9em; margin-left: 8px; }}
        @media (max-width: 768px) {{ .container {{ padding: 15px; }} h1 {{ font-size: 1.5em; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {content}
    </div>
</body>
</html>"""

def get_latest_articles(feed_url, time_delta_hours=144):
    latest_articles = []
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=FEED_TIMEOUT) as response:
            feed = feedparser.parse(response.read())
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

def generate_html(articles_by_date, output_path):
    content_parts = []
    china_tz = timezone(timedelta(hours=8))
    today_str = datetime.now(china_tz).strftime('%Y-%m-%d')

    sorted_dates = sorted(articles_by_date.keys(), key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)

    if today_str in sorted_dates:
        sorted_dates.remove(today_str)
        sorted_dates.insert(0, today_str)
    elif sorted_dates:
        content_parts.append(f"<h2>{today_str} (today)</h2>")
        content_parts.append("<p>No updates at this time</p>")

    for date_str in sorted_dates:
        articles_by_category = articles_by_date[date_str]
        date_display = f"{date_str} (today)" if date_str == today_str else f"{date_str}"
        content_parts.append(f"<h2>{date_display}</h2>")

        categories = sorted(articles_by_category.keys())
        show_category_labels = len(categories) > 1

        for category in categories:
            articles = articles_by_category[category]
            if show_category_labels:
                content_parts.append(f"<h3>{category}</h3>")
            content_parts.append("<ul>")
            for article in sorted(articles, key=lambda x: x['published_dt'], reverse=True):
                content_parts.append(f"<li><a href='{html.escape(article['link'])}'>{html.escape(article['title'])}</a> <span>({article['time_str']})</span></li>")
            content_parts.append("</ul>")

    full_content = "".join(content_parts) if content_parts else "<p>No articles found in the last 6 days.</p>"
    html_output = HTML_TEMPLATE.replace('{title}', 'RSS Page').replace('{content}', full_content)

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

    feed_tasks = []
    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            if feed_url.strip():
                feed_tasks.append((category, feed_url))

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

    generate_html(articles_by_date, output_file)

if __name__ == '__main__':
    main()
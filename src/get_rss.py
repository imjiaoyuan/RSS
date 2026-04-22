import os
import sys
import feedparser
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import RSS_FEEDS

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
        feed = feedparser.parse(feed_url)
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(hours=time_delta_hours)
        
        for entry in feed.entries:
            published_time = entry.get('published_parsed')
            if not published_time:
                continue
            published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)
            
            if published_dt > now:
                continue
            if published_dt >= time_threshold:
                latest_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published_dt': published_dt,
                    'date_str': published_dt.strftime('%Y-%m-%d'),
                    'time_str': published_dt.strftime('%H:%M'),
                    'category': None
                })
    except Exception:
        pass
    return latest_articles

def generate_html(articles_by_date, output_path):
    content_parts = []
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    sorted_dates = sorted(articles_by_date.keys(), key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)
    
    if today_str in sorted_dates:
        sorted_dates.remove(today_str)
        sorted_dates.insert(0, today_str)
    
    for date_str in sorted_dates:
        articles_by_category = articles_by_date[date_str]
        date_display = f"{date_str} (today)" if date_str == today_str else f"{date_str}"
        content_parts.append(f"<h2>{date_display}</h2>")
        
        for category in sorted(articles_by_category.keys()):
            articles = articles_by_category[category]
            content_parts.append(f"<h3>{category}</h3>")
            content_parts.append("<ul>")
            for article in sorted(articles, key=lambda x: x['published_dt'], reverse=True):
                content_parts.append(f"<li><a href='{article['link']}'>{article['title']}</a> <span>({article['time_str']})</span></li>")
            content_parts.append("</ul>")
    
    full_content = "".join(content_parts) if content_parts else "<p>No articles found in the last 3 days.</p>"
    html = HTML_TEMPLATE.replace('{title}', 'RSS Page').replace('{content}', full_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    if len(sys.argv) < 2:
        output_dir = "public"
    else:
        output_dir = sys.argv[1]

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'index.html')

    articles_by_date = {}
    
    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            articles = get_latest_articles(feed_url)
            for article in articles:
                article['category'] = category
                date_str = article['date_str']
                if date_str not in articles_by_date:
                    articles_by_date[date_str] = {}
                if category not in articles_by_date[date_str]:
                    articles_by_date[date_str][category] = []
                articles_by_date[date_str][category].append(article)
    
    generate_html(articles_by_date, output_file)

if __name__ == '__main__':
    main()
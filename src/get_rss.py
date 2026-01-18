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

def get_latest_articles(feed_url, time_delta_hours=72):
    latest_articles = []
    try:
        feed = feedparser.parse(feed_url)
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=time_delta_hours)
        for entry in feed.entries:
            published_time = entry.get('published_parsed')
            if not published_time:
                continue
            published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)
            if published_dt >= time_threshold:
                latest_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published_dt': published_dt,
                    'date_str': published_dt.strftime('%Y-%m-%d'),
                    'time_str': published_dt.strftime('%H:%M')
                })
    except Exception:
        pass
    return latest_articles

def generate_html(articles_by_date_category, output_path):
    content_parts = []
    
    for date_str, categories in sorted(articles_by_date_category.items(), reverse=True):
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        date_display = f"{date_str} (today)" if date_str == today_str else f"{date_str}"
        content_parts.append(f"<h2>{date_display}</h2>")
        
        for category, articles in categories.items():
            if articles:
                content_parts.append(f"<h3>{category}</h3>")
                content_parts.append("<ul>")
                for article in articles:
                    content_parts.append(f"<li><a href='{article['link']}'>{article['title']}</a> <span>({article['time_str']})</span></li>")
                content_parts.append("</ul>")
    
    full_content = "".join(content_parts) if content_parts else "<p>No articles found in the last 3 days.</p>"
    html = HTML_TEMPLATE.replace('{title}', 'RSS Pages').replace('{content}', full_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    if len(sys.argv) < 2:
        output_dir = "public"
    else:
        output_dir = sys.argv[1]

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'index.html')

    all_articles = []
    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            articles = get_latest_articles(feed_url)
            for article in articles:
                article['category'] = category
                all_articles.append(article)
    
    articles_by_date_category = {}
    
    for article in all_articles:
        date_str = article['date_str']
        category = article['category']
        
        if date_str not in articles_by_date_category:
            articles_by_date_category[date_str] = {}
        
        if category not in articles_by_date_category[date_str]:
            articles_by_date_category[date_str][category] = []
        
        articles_by_date_category[date_str][category].append(article)
    
    for date_str in articles_by_date_category:
        for category in articles_by_date_category[date_str]:
            articles_by_date_category[date_str][category].sort(key=lambda x: x['published_dt'], reverse=True)
    
    generate_html(articles_by_date_category, output_file)

if __name__ == '__main__':
    main()
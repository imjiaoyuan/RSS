import feedparser
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header
from config import RSS_FEEDS, EMAIL_CONFIG

def get_latest_articles(feed_url, time_delta_hours=24):
    latest_articles = []
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
                'published': published_dt.strftime('%Y-%m-%d %H:%M')
            })
    return latest_articles

def create_html_content(articles_by_category):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 15px; }}
            h1 {{ font-size: 22px; }}
            h2 {{ font-size: 19px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
            ul {{ list-style-type: disc; padding-left: 25px; }}
            li {{ margin-bottom: 12px; }}
            a, a:visited {{
                color: #007BFF;
                text-decoration: none;
                font-size: 16px;
            }}
            a:hover {{ text-decoration: underline; }}
            .published-time {{ color: #888; font-size: 0.9em; }}
        </style>
    </head>
    <body><h1>RSS Update</h1>
    """
    for category_key, articles in articles_by_category.items():
        if articles:
            display_name = category_key
            html_content += f"<h2>{display_name}</h2><ul>"
            for article in articles:
                html_content += f"<li><a href='{article['link']}' target='_blank'>{article['title']}</a> <span class='published-time'>({article['published']})</span></li>"
            html_content += "</ul>"
    html_content += "</body></html>"
    return html_content

def send_email(subject, html_content, config):
    receivers = config.get('receiver_emails', [])
    if not receivers:
        print("No recipients configured. Skipping email.")
        return
    message = MIMEText(html_content, 'html', 'utf-8')
    message['From'] = config['sender_email']
    message['To'] = ", ".join(receivers)
    message['Subject'] = Header(subject, 'utf-8')
    server = None
    try:
        print("Connecting to SMTP server...")
        server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        server.login(config['sender_email'], config['sender_password'])
        server.sendmail(config['sender_email'], receivers, message.as_string())
        print(f"Email sent successfully to: {', '.join(receivers)}")
    except smtplib.SMTPException as e:
        print(f"Failed to send email. SMTP Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if server:
            try:
                server.quit()
            except smtplib.SMTPServerDisconnected:
                pass

def main():
    print("Starting RSS fetch job...")
    all_new_articles = {}
    total_new_count = 0
    for category, feeds in RSS_FEEDS.items():
        print(f"Processing category: {category}")
        category_articles = []
        for feed_url in feeds:
            try:
                articles = get_latest_articles(feed_url)
                if articles:
                    category_articles.extend(articles)
            except Exception as e:
                print(f"  - Failed to fetch {feed_url[:70]}... Error: {e}")
        if category_articles:
            category_articles.sort(key=lambda x: x['published'], reverse=True)
            all_new_articles[category] = category_articles
            total_new_count += len(category_articles)
    print("Fetch job complete.")
    if total_new_count > 0:
        print(f"Found {total_new_count} new articles. Preparing to send email.")
        html_body = create_html_content(all_new_articles)
        send_email("RSS Update", html_body, EMAIL_CONFIG)
    else:
        print("No new articles found. No email will be sent.")

if __name__ == '__main__':
    main()
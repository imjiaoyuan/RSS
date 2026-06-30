import re
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

from utils import fetch_url, FEED_TIMEOUT

ROUTE_CONFIG = {
    "name": "sspai_matrix",
    "label": "Matrix",
    "url": "https://sspai.com/matrix",
    "description": "少数派 Matrix 社区",
}

CHINA_TZ = timezone(timedelta(hours=8))
UTC_TZ = timezone.utc


def _parse_date(raw: str) -> datetime | None:
    now_cn = datetime.now(CHINA_TZ)
    raw = raw.strip()

    if "/" not in raw and ":" in raw:
        hour, minute = map(int, raw.split(":"))
        dt = now_cn.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "/" in raw:
        parts = raw.split()
        month, day = map(int, parts[0].split("/"))
        hour, minute = map(int, parts[1].split(":"))
        dt = datetime(now_cn.year, month, day, hour, minute, tzinfo=CHINA_TZ)
        if dt > now_cn:
            dt = datetime(now_cn.year - 1, month, day, hour, minute, tzinfo=CHINA_TZ)
    else:
        return None

    return dt.astimezone(UTC_TZ)


def _parse_articles(html: str) -> list[dict]:
    articles: list[dict] = []

    for li_html in re.findall(
        r'<li class="posts-list-item"[^>]*>(.*?)</li>', html, re.DOTALL
    ):
        id_m = re.search(r'href="/post/(\d+)"', li_html)
        if not id_m:
            continue
        post_id = id_m.group(1)

        title_m = re.search(r'<div class="post-title"[^>]*>(.*?)</div>', li_html)
        if not title_m:
            continue
        title = title_m.group(1).strip()

        author_m = re.search(
            r'post-author-name[^>]*>.*?<span[^>]*>(.*?)</span>', li_html, re.DOTALL
        )
        author = author_m.group(1).strip() if author_m else ""

        raw_date = ""
        for span in re.findall(
            r'<span class="post-other-item"[^>]*>(.*?)</span>', li_html, re.DOTALL
        ):
            if "<i " not in span:
                m = re.search(r'>([^<]+)$', span)
                if m:
                    raw_date = m.group(1).strip()
                    break

        if not raw_date:
            continue

        published_dt = _parse_date(raw_date)
        if published_dt is None:
            continue

        china_dt = published_dt.astimezone(CHINA_TZ)

        articles.append({
            "title": title,
            "link": f"https://sspai.com/post/{post_id}",
            "published_dt": published_dt,
            "date_str": china_dt.strftime("%Y-%m-%d"),
            "time_str": china_dt.strftime("%H:%M"),
        })

    return articles


def fetch(config: dict | None = None) -> list[dict]:
    url = (config or ROUTE_CONFIG)["url"]
    html = fetch_url(url, timeout=FEED_TIMEOUT).decode("utf-8")

    articles = _parse_articles(html)
    now = datetime.now(UTC_TZ)
    cutoff = now - timedelta(hours=144)
    articles = [a for a in articles if a["published_dt"] >= cutoff]
    logger.info(f"sspai_matrix: fetched {len(articles)} articles")
    return articles


if __name__ == "__main__":
    import json, sys, argparse

    parser = argparse.ArgumentParser(description="Scrape 少数派 Matrix")
    parser.add_argument("--days", type=int, default=6)
    parser.add_argument("--rss", action="store_true")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    articles = fetch()

    now = datetime.now(UTC_TZ)
    cutoff = now - timedelta(days=args.days)
    articles = [a for a in articles if a["published_dt"] >= cutoff]

    if args.rss:
        import html as html_mod
        def _rfc822(dt):
            return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        items = []
        for a in articles:
            pub_dt = a["published_dt"]
            items.append(
                f'  <item>\n'
                f'    <title>{html_mod.escape(a["title"])}</title>\n'
                f'    <link>{html_mod.escape(a["link"])}</link>\n'
                f'    <description>作者：{html_mod.escape(a.get("author", ""))}｜{a["time_str"]}</description>\n'
                f'    <pubDate>{_rfc822(pub_dt)}</pubDate>\n'
                f'    <guid isPermaLink="true">{html_mod.escape(a["link"])}</guid>\n'
                f'  </item>'
            )
        output = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            '<channel>\n'
            '  <title>少数派 Matrix</title>\n'
            '  <link>https://sspai.com/matrix</link>\n'
            f'  <lastBuildDate>{_rfc822(now)}</lastBuildDate>\n'
            + "\n".join(items) + '\n'
            '</channel>\n</rss>'
        )
    else:
        output = json.dumps([{**a, "published_dt": a["published_dt"].isoformat()}
                             for a in articles],
                            ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(articles)} articles to {args.output}", file=sys.stderr)
    else:
        print(output)

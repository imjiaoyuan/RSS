"""One-off health check for all feeds in config.RSS_FEEDS.

For each feed: fetch, parse, count entries within the last 144 hours.
Prints a compact table; exit code is always 0.
"""
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
import feedparser

from config import RSS_FEEDS
from utils import fetch_url

NOW = datetime.now(timezone.utc)
THRESHOLD = NOW - timedelta(hours=144)


def check(feed_url):
    t0 = time.monotonic()
    try:
        data = fetch_url(feed_url)
        feed = feedparser.parse(data)
    except Exception as e:
        return feed_url, 'ERR', 0, 0, round(time.monotonic() - t0), str(e)[:60]
    if feed.bozo and not feed.entries:
        return feed_url, 'BAD', 0, 0, round(time.monotonic() - t0), str(feed.bozo_exception)[:60]
    total = len(feed.entries)
    recent = 0
    for e in feed.entries:
        ts = e.get('published_parsed') or e.get('updated_parsed')
        if not ts:
            continue
        dt = datetime(*ts[:6], tzinfo=timezone.utc)
        if THRESHOLD <= dt <= NOW:
            recent += 1
    return feed_url, 'OK', recent, total, round(time.monotonic() - t0), ''


def main():
    urls = [u for feeds in RSS_FEEDS.values() for u in feeds
            if u.startswith('http')]
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(check, u): u for u in urls}
        for f in as_completed(futs):
            results.append(f.result())
    results.sort(key=lambda r: (r[1], r[3]))
    print(f"{'status':6} {'144h':>5} {'total':>6} {'sec':>4}  url / note")
    for url, st, recent, total, sec, note in results:
        line = f"{st:6} {recent:5} {total:6} {sec:4}  {url}"
        if note:
            line += f"   [{note}]"
        print(line)
    ok = sum(1 for r in results if r[1] == 'OK')
    empty = sum(1 for r in results if r[1] == 'OK' and r[2] == 0)
    print(f"\n{len(results)} feeds: {ok} ok, {empty} ok but 0 entries in 144h,"
          f" {len(results) - ok} failed")


if __name__ == '__main__':
    main()

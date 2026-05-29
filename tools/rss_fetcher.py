# tools/rss_fetcher.py
import os
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.feeds import RSS_FEEDS
from db.store import get_known_urls

MAX_PER_FEED  = int(os.getenv("MAX_PER_FEED", 5))       # max NEW articles taken per feed
FETCH_TIMEOUT = int(os.getenv("FEED_FETCH_TIMEOUT", 10))  # hard per-feed timeout (seconds)
FETCH_WORKERS = int(os.getenv("FEED_FETCH_WORKERS", 12))  # feeds fetched concurrently

# A browser-like UA. Many feeds (Reddit, some CDNs) reject the default
# python/feedparser agent with 403/429.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 NewsWatchdog/1.0"
)


def _fetch_one(category: str, feed_url: str) -> tuple[str, list[dict]]:
    """Fetch and parse a single feed with a hard timeout. Network/parse errors
    raise — the caller logs them and moves on. Returns (feed_url, [articles])."""
    resp = requests.get(
        feed_url,
        timeout=FETCH_TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"},
    )
    resp.raise_for_status()

    feed = feedparser.parse(resp.content)
    source = feed.feed.get("title", feed_url)

    items = []
    for entry in feed.entries:
        url = entry.get("link", "")
        title = entry.get("title", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        if not url or not title:
            continue
        items.append({
            "title": title,
            "url": url,
            "summary": summary[:500],
            "source": source,
            "category": category,
        })
        # Small buffer beyond MAX_PER_FEED so dedup in the caller still has
        # enough fresh candidates to hit the per-feed cap.
        if len(items) >= MAX_PER_FEED * 3:
            break
    return feed_url, items


def fetch_articles(max_total: int = 270) -> list[dict]:
    """
    Fetch every feed in parallel (each with a hard timeout so a blocked/slow feed
    can't stall the cycle), tag articles with their category, and dedup against the
    DB in a single query. Caps NEW articles at MAX_PER_FEED per feed and max_total
    overall. Feeds that fail (blocked, 4xx/5xx, timeout) are logged and skipped.
    """
    known = get_known_urls()   # one DB read instead of one per candidate article
    seen: set[str] = set()
    collected: list[dict] = []

    jobs = [(cat, url) for cat, urls in RSS_FEEDS.items() for url in urls]
    ok = failed = 0

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        futures = {ex.submit(_fetch_one, cat, url): (cat, url) for cat, url in jobs}
        for fut in as_completed(futures):
            cat, feed_url = futures[fut]
            try:
                _, items = fut.result()
                ok += 1
            except Exception as e:
                failed += 1
                print(f"[RSS] Failed to fetch {feed_url}: {e}")
                continue

            taken = 0
            for art in items:
                if taken >= MAX_PER_FEED:
                    break
                u = art["url"]
                if u in known or u in seen:   # already in DB, or already taken this run
                    continue
                seen.add(u)
                collected.append(art)
                taken += 1

    print(f"[RSS] Feeds OK: {ok}, failed: {failed}, new articles: {len(collected)}")
    return collected[:max_total]

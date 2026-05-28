# tools/rss_fetcher.py
import feedparser
from config.feeds import RSS_FEEDS
from db.store import already_checked

MAX_PER_FEED = 5  # max articles taken from each individual feed per cycle


def fetch_articles(max_total: int = 270) -> list[dict]:
    """
    Visits every feed in every category. Tags each article with its category.
    Collects up to MAX_PER_FEED articles per feed so no single feed hogs the quota.
    All feeds are always visited — no feed is skipped because an earlier one filled up.
    Returns up to max_total articles total.
    """
    articles = []

    for category, urls in RSS_FEEDS.items():
        for feed_url in urls:
            feed_count = 0
            try:
                feed = feedparser.parse(feed_url)
                source = feed.feed.get("title", feed_url)

                for entry in feed.entries:
                    if feed_count >= MAX_PER_FEED:
                        break

                    url = entry.get("link", "")
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", entry.get("description", "")).strip()

                    if not url or not title:
                        continue
                    if already_checked(url):
                        continue

                    articles.append({
                        "title": title,
                        "url": url,
                        "summary": summary[:500],
                        "source": source,
                        "category": category,
                    })
                    feed_count += 1

            except Exception as e:
                print(f"[RSS] Failed to fetch {feed_url}: {e}")

    return articles[:max_total]

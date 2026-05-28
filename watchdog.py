# watchdog.py  —  main entry point

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import logging

# Must be set before crewai/litellm are imported
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["LITELLM_DISABLE_PROMPT_CACHING"] = "true"
os.environ["GROQ_DISABLE_CACHING"] = "true"

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

load_dotenv()

from db.store import (
    init_db, save_article, save_verdict,
    mark_alerted, mark_triaged, get_next_triaged,
    clear_old_articles,
)
from tools.rss_fetcher import fetch_articles
from tools.telegram_alert import send_alert
from agents.crew_runner import run_triage, investigate_article
import litellm
litellm.disable_cache = True
os.environ["GROQ_DISABLE_CACHING"] = "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("watchdog")

MAX_ARTICLES      = int(os.getenv("MAX_ARTICLES_PER_RUN", 270))
FETCH_INTERVAL_MIN = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", 120))
ALERT_INTERVAL_MIN = int(os.getenv("ALERT_INTERVAL_MINUTES", 15))
PORT               = int(os.getenv("PORT", 8080))

app = Flask(__name__)


@app.route("/")
def health():
    return "News Watchdog is running.", 200


def run_cycle():
    """Every 2 hours: fetch RSS → triage → mark top articles as pending."""
    log.info("=" * 50)
    log.info("Fetch cycle started")

    deleted = clear_old_articles(hours=24)
    if deleted:
        log.info(f"Cleared {deleted} articles older than 24 hours")

    articles = fetch_articles(max_total=MAX_ARTICLES)
    log.info(f"Fetched {len(articles)} new articles across all feeds")

    if not articles:
        log.info("Nothing new — feeds haven't updated yet.")
        return

    for a in articles:
        save_article(a["url"], a["title"], a["source"], a.get("category", ""))

    log.info("Running triage (1 pick per category)...")
    flagged = run_triage(articles)
    log.info(f"Triage selected {len(flagged)} articles ({', '.join(a['category'] for a in flagged)})")

    for a in flagged:
        mark_triaged(a["url"])

    log.info("Fetch cycle complete — articles queued for investigation.")


def investigate_and_alert():
    """Every 15 minutes: investigate 1 pending article → send Telegram alert."""
    row = get_next_triaged()
    if not row:
        log.info("[Alert] No pending articles to investigate.")
        return

    url, title, source, category, summary = row
    log.info(f"[Alert] Investigating: {title[:80]}")

    article = {"url": url, "title": title, "source": source,
               "category": category, "summary": summary or ""}
    try:
        result = investigate_article(article)
        verdict    = result["verdict"]
        confidence = result["confidence"]
        rep_summary = result["summary"]

        save_verdict(url, verdict, confidence, rep_summary)
        log.info(f"[Alert]  → {verdict} ({confidence}%)")

        send_alert(
            title=title, source=source,
            verdict=verdict, confidence=confidence,
            summary=rep_summary, url=url,
        )
        mark_alerted(url)

    except Exception as e:
        log.error(f"[Alert] Investigation failed: {e}")


def main():
    init_db()
    log.info(f"News Watchdog started.")
    log.info(f"Fetch: every {FETCH_INTERVAL_MIN} min | Alert: every {ALERT_INTERVAL_MIN} min")

    # Run first fetch immediately in background
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_cycle,             "interval", minutes=FETCH_INTERVAL_MIN)
    scheduler.add_job(investigate_and_alert, "interval", minutes=ALERT_INTERVAL_MIN)
    scheduler.start()

    run_cycle()  # immediate first run

    # Flask keeps the process alive and satisfies Render's health check
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()

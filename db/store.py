import sqlite3
import os
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "watchdog.db")


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT UNIQUE NOT NULL,
            title       TEXT,
            source      TEXT,
            category    TEXT,
            fetched_at  TEXT,
            triaged     INTEGER DEFAULT 0,
            verdict     TEXT,
            confidence  INTEGER,
            summary     TEXT,
            alerted     INTEGER DEFAULT 0
        )
    """)
    # Add columns if upgrading from an older schema
    for col, definition in [("category", "TEXT"), ("triaged", "INTEGER DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE articles ADD COLUMN {col} {definition}")
        except Exception:
            pass
    con.commit()
    con.close()


def already_checked(url: str) -> bool:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    found = cur.fetchone() is not None
    con.close()
    return found


def save_article(url: str, title: str, source: str, category: str = ""):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO articles (url, title, source, category, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (url, title, source, category, datetime.now(timezone.utc).isoformat()),
        )
        con.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        con.close()


def mark_triaged(url: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE articles SET triaged = 1 WHERE url = ?", (url,))
    con.commit()
    con.close()


def get_next_triaged():
    """Return the next triaged article that hasn't been investigated yet (FIFO)."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """SELECT url, title, source, category, summary
           FROM articles
           WHERE triaged = 1 AND verdict IS NULL
           ORDER BY fetched_at ASC
           LIMIT 1"""
    )
    row = cur.fetchone()
    con.close()
    return row  # (url, title, source, category, summary) or None


def save_verdict(url: str, verdict: str, confidence: int, summary: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "UPDATE articles SET verdict = ?, confidence = ?, summary = ? WHERE url = ?",
        (verdict, confidence, summary, url),
    )
    con.commit()
    con.close()


def mark_alerted(url: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE articles SET alerted = 1 WHERE url = ?", (url,))
    con.commit()
    con.close()


def clear_old_articles(hours: int = 24):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM articles WHERE fetched_at < ?", (cutoff,))
    deleted = cur.rowcount
    con.commit()
    con.close()
    return deleted


def get_recent_verdicts(limit: int = 20):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """SELECT title, source, verdict, confidence, summary, fetched_at
           FROM articles WHERE verdict IS NOT NULL
           ORDER BY fetched_at DESC LIMIT ?""",
        (limit,),
    )
    rows = cur.fetchall()
    con.close()
    return rows

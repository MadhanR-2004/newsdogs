# 📡 News Watchdog

A CrewAI-powered agent that continuously monitors RSS feeds, triages suspicious headlines,
and fact-checks them using a multi-agent pipeline — then alerts you on Telegram.

## Architecture

```
RSS Feeds → Triage Agent → [Believer + Skeptic] → Judge → Reporter → Telegram Alert
                                    ↓
                               SQLite (dedup + verdicts)
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | How to get it |
|---|---|
| `GROQ_API_KEY` | https://console.groq.com → API Keys |
| `TELEGRAM_BOT_TOKEN` | Message @BotFather on Telegram → /newbot |
| `TELEGRAM_CHAT_ID` | Message @userinfobot on Telegram |
| `SERPER_API_KEY` | https://serper.dev → free 2500 searches |

### 3. Run
```bash
python watchdog.py
```

### 4. View stored verdicts
```bash
python view_results.py
```

## Tuning (in .env)

| Variable | Default | Description |
|---|---|---|
| `SCHEDULE_INTERVAL_MINUTES` | 30 | How often to check feeds |
| `MAX_ARTICLES_PER_RUN` | 20 | Max articles fetched per cycle |
| `TRIAGE_PICK_TOP` | 5 | How many articles to investigate |
| `CONFIDENCE_ALERT_THRESHOLD` | 40 | Alert if confidence < this % |

## Adding RSS feeds
Edit `config/feeds.py` and add any RSS URL to the `RSS_FEEDS` list.

## Verdict logic
- `REAL` → high confidence supporting evidence found
- `FAKE` → strong counter-evidence, always alerts
- `UNVERIFIED` → conflicting/insufficient evidence
  - Alerts only if confidence < threshold

## Project structure
```
news-watchdog/
├── watchdog.py          # main entry point + scheduler
├── view_results.py      # CLI to inspect verdicts
├── requirements.txt
├── .env.example
├── config/
│   └── feeds.py         # RSS feed URLs
├── db/
│   └── store.py         # SQLite layer
├── tools/
│   ├── rss_fetcher.py   # fetches + deduplicates articles
│   └── telegram_alert.py
└── agents/
    ├── crew_agents.py   # agent definitions
    └── crew_runner.py   # task/crew orchestration
```

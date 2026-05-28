import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

VERDICT_EMOJI = {
    "FAKE": "🚨",
    "REAL": "✅",
    "UNVERIFIED": "⚠️",
}

def send_alert(title: str, source: str, verdict: str, confidence: int, summary: str, url: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[Telegram] Not configured — skipping alert.")
        return

    emoji = VERDICT_EMOJI.get(verdict.upper(), "❓")
    confidence_bar = "█" * round(confidence / 10) + "░" * (10 - round(confidence / 10))

    message = (
        f"{emoji} {verdict.upper()} — {confidence}% confidence\n"
        f"{confidence_bar}\n\n"
        f"{title}\n"
        f"Source: {source}\n\n"
        f"{summary[:300]}\n\n"
        f"{url}"
    )

    url_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    try:
        resp = requests.post(url_api, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[Telegram] Alert sent: {title[:60]}")
    except Exception as e:
        print(f"[Telegram] Failed to send alert: {e}")

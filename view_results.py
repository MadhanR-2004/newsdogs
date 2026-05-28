# view_results.py  —  quick CLI to inspect stored verdicts
from db.store import init_db, get_recent_verdicts

COLORS = {
    "FAKE": "\033[91m",       # red
    "REAL": "\033[92m",       # green
    "UNVERIFIED": "\033[93m", # yellow
    "RESET": "\033[0m",
}

def bar(confidence: int) -> str:
    filled = round(confidence / 10)
    return "█" * filled + "░" * (10 - filled)

def main():
    init_db()
    rows = get_recent_verdicts(limit=20)

    if not rows:
        print("No verdicts yet. Run watchdog.py first.")
        return

    print(f"\n{'='*70}")
    print(f"  NEWS WATCHDOG — Last {len(rows)} Verdicts")
    print(f"{'='*70}\n")

    for title, source, verdict, confidence, summary, fetched_at in rows:
        color = COLORS.get(verdict or "UNVERIFIED", "")
        reset = COLORS["RESET"]
        conf = confidence or 0

        print(f"{color}[{verdict}]{reset} {conf}% {bar(conf)}")
        print(f"  {title}")
        print(f"  Source: {source}  |  {fetched_at[:16]}")
        if summary:
            print(f"  {summary[:200]}...")
        print()

if __name__ == "__main__":
    main()

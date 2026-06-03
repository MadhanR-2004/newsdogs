# tools/web_search.py
"""Direct Serper search, called from Python — NOT exposed to the agents as a tool.

Groq's llama-3.3 tool-calling is unreliable (it intermittently emits malformed
function calls → Groq 'tool_use_failed'). So instead of letting the agents call a
search tool, we fetch results here and inject them into the prompts. The agents
have no tools, so there are no function calls that can fail. Search errors (e.g. a
bad/expired Serper key, 403, quota) degrade gracefully to an empty string."""
import os
import requests

SERPER_URL = "https://google.serper.dev/search"
SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", 15))


def web_search(query: str, n: int = 6) -> str:
    """Return up to `n` organic results formatted as bullet lines, or "" on any
    failure (missing key, auth error, network, quota)."""
    key = os.getenv("SERPER_API_KEY")
    if not key:
        print("[Search] SERPER_API_KEY not set — skipping web search.")
        return ""

    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": n},
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Search] Serper request failed: {e}")
        return ""

    lines = []
    for item in data.get("organic", [])[:n]:
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()
        link = item.get("link", "").strip()
        if title and link:
            lines.append(f"- {title}: {snippet} ({link})")
    return "\n".join(lines)

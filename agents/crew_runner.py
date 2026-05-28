# agents/crew_runner.py
import os
import re
import time
from crewai import Task, Crew, Process
from agents.crew_agents import make_agents

triage_top = int(os.getenv("TRIAGE_PICK_TOP", 5))


def run_triage(articles: list[dict]) -> list[dict]:
    """
    Category-based triage: for each category that has articles, the LLM picks
    the single most suspicious headline. Returns 1 article per active category.
    """
    if not articles:
        return []

    # Group articles by category, preserving original indices
    by_category: dict[str, list[tuple[int, dict]]] = {}
    for i, a in enumerate(articles):
        by_category.setdefault(a["category"], []).append((i, a))

    triage, _, _, _, _ = make_agents()

    # Build a prompt that shows articles grouped under their category headings
    lines = []
    for cat, items in by_category.items():
        lines.append(f"\n[{cat}]")
        for idx, a in items:
            lines.append(f"  {idx + 1}. {a['title']}")

    headlines_text = "\n".join(lines)
    num_cats = len(by_category)

    task = Task(
        description=(
            f"Below are news headlines grouped by category:\n"
            f"{headlines_text}\n\n"
            f"For EACH of the {num_cats} categories, pick the ONE headline that is most "
            "suspicious, misleading, or worth fact-checking. "
            "Respond with ONLY a comma-separated list of article numbers — exactly one per category "
            "(e.g. 3,12,19,24,31,45)."
        ),
        expected_output=f"Comma-separated list of {num_cats} article numbers, one per category.",
        agent=triage,
    )

    crew = Crew(agents=[triage], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    output = str(result).strip()

    # Parse LLM picks
    picked_indices = []
    for token in re.findall(r"\d+", output):
        idx = int(token) - 1
        if 0 <= idx < len(articles):
            picked_indices.append(idx)

    # Deduplicate while preserving order
    picked_indices = list(dict.fromkeys(picked_indices))

    # Fallback: if LLM missed a category, add the first article from it
    covered = {articles[i]["category"] for i in picked_indices}
    for cat, items in by_category.items():
        if cat not in covered:
            picked_indices.append(items[0][0])

    return [articles[i] for i in picked_indices]


def investigate_article(article: dict, attempts: int = 3) -> dict:
    """
    Run the full believer → skeptic → judge → reporter pipeline on one article.
    Retries up to `attempts` times on transient failures (rate limits, API errors).
    Returns {verdict, confidence, summary}.
    """
    for attempt in range(attempts):
        try:
            return _run_pipeline(article)
        except Exception as e:
            if attempt == attempts - 1:
                raise
            wait = 30 * (attempt + 1)
            print(f"[crew] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)


def _run_pipeline(article: dict) -> dict:
    _, believer, skeptic, judge, reporter = make_agents()

    claim = f"'{article['title']}' (Source: {article['source']})\n\nContext: {article['summary']}"

    t_believe = Task(
        description=(
            f"Research and find the strongest SUPPORTING evidence for this claim:\n{claim}\n\n"
            "List bullet points with source URLs. Be specific — no vague statements."
        ),
        expected_output="Bullet list of supporting evidence with source URLs.",
        agent=believer,
    )

    t_skeptic = Task(
        description=(
            f"Research and find the strongest COUNTER evidence against this claim:\n{claim}\n\n"
            "List bullet points with source URLs. Be specific — no vague statements."
        ),
        expected_output="Bullet list of counter-evidence with source URLs.",
        agent=skeptic,
    )

    t_judge = Task(
        description=(
            "You have been given supporting evidence and counter-evidence for a news claim.\n"
            "Weigh them carefully and respond in EXACTLY this format:\n\n"
            "VERDICT: <REAL|FAKE|UNVERIFIED>\n"
            "CONFIDENCE: <0-100>\n"
            "REASON: <one sentence explaining your verdict>"
        ),
        expected_output="VERDICT, CONFIDENCE, and REASON in the specified format.",
        agent=judge,
        context=[t_believe, t_skeptic],
    )

    t_report = Task(
        description=(
            "Write a 3-sentence plain-language summary of this fact-check investigation. "
            "End with the verdict clearly stated. Keep it under 100 words."
        ),
        expected_output="3-sentence summary ending with the verdict.",
        agent=reporter,
        context=[t_judge],
    )

    crew = Crew(
        agents=[believer, skeptic, judge, reporter],
        tasks=[t_believe, t_skeptic, t_judge, t_report],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    tasks_out = result.tasks_output  # [believe, skeptic, judge, reporter]

    judge_raw = tasks_out[2].raw if len(tasks_out) > 2 else ""
    reporter_raw = tasks_out[3].raw if len(tasks_out) > 3 else str(result)

    verdict = "UNVERIFIED"
    confidence = 50

    verdict_match = re.search(r"VERDICT:\s*(REAL|FAKE|UNVERIFIED)", judge_raw, re.IGNORECASE)
    confidence_match = re.search(r"CONFIDENCE:\s*(\d+)", judge_raw, re.IGNORECASE)

    if verdict_match:
        verdict = verdict_match.group(1).upper()
    if confidence_match:
        confidence = int(confidence_match.group(1))

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": reporter_raw.strip(),
    }

# agents/crew_agents.py
import os

# Must be set BEFORE crewai/litellm are imported. This stops LiteLLM from
# injecting Anthropic-style cache_control breakpoints into the prompt, which
# Groq rejects with a 400 BadRequestError. (setdefault so watchdog.py / .env win.)
os.environ.setdefault("LITELLM_DISABLE_PROMPT_CACHING", "true")

from crewai import Agent, LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

# crewai 1.14.5 tags the system/user prompt with a `cache_breakpoint` flag for
# prompt caching, but its Groq (litellm) path never strips that flag — so Groq
# rejects the request: "property 'cache_breakpoint' is unsupported". Groq has no
# prompt-caching API, so the marker is pure liability. Replace crewai's
# mark_cache_breakpoint with a strip-only no-op. The executors import this function
# at call time (inside the method), so patching the module attribute takes effect.
# NOTE: this is the real fix for the Groq 400 — it must live in our code so it
# ships to Render; editing the installed crewai file would not survive a fresh deploy.
import crewai.llms.cache as _crew_cache


def _strip_cache_breakpoint(message: dict) -> dict:
    return {k: v for k, v in message.items() if k != _crew_cache.CACHE_BREAKPOINT_KEY}


_crew_cache.mark_cache_breakpoint = _strip_cache_breakpoint

load_dotenv()

# Do NOT pass cache=False here: crewai forwards it to litellm.completion(), which
# expects `cache` to be a dict and crashes with
#   AttributeError: 'bool' object has no attribute 'get'
# Prompt caching is disabled via LITELLM_DISABLE_PROMPT_CACHING above instead.
llm = LLM(model="groq/llama-3.3-70b-versatile")
search_tool = SerperDevTool(n_results=3)

# Agents are created once at import time and reused across all pipeline calls.
_agents = None


def make_agents():
    global _agents
    if _agents is not None:
        return _agents

    triage = Agent(
        role="News Triage Analyst",
        goal=(
            "From a list of news headlines, identify the ones that are most likely "
            "to be misleading, sensational, or factually suspicious."
        ),
        backstory=(
            "You are a senior editor at a fact-checking organization. "
            "You have a sharp nose for clickbait, propaganda, and misinformation. "
            "You read headlines and quickly identify which ones deserve deeper scrutiny."
        ),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    believer = Agent(
        role="Claim Supporter",
        goal="Find the strongest factual evidence that SUPPORTS the news claim being true.",
        backstory=(
            "You are a researcher who genuinely believes the claim might be true. "
            "You search for credible sources, official statements, data, and expert opinions "
            "that support the claim. You only cite real, verifiable sources."
        ),
        llm=llm,
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
    )

    skeptic = Agent(
        role="Claim Debunker",
        goal="Find the strongest factual evidence that CONTRADICTS or DISPROVES the news claim.",
        backstory=(
            "You are a hardcore fact-checker and skeptic. Your job is to tear apart the claim "
            "with evidence. You look for official rebuttals, contradicting data, source credibility "
            "issues, and prior misinformation patterns from the same outlet."
        ),
        llm=llm,
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
    )

    judge = Agent(
        role="Verdict Judge",
        goal=(
            "Weigh the supporting and contradicting evidence and deliver a final verdict: "
            "REAL, FAKE, or UNVERIFIED — with a confidence percentage (0-100) and a brief reasoning."
        ),
        backstory=(
            "You are a neutral, evidence-driven judge. You do not have personal opinions. "
            "You only rule based on the quality and quantity of verified evidence presented to you. "
            "You always output your verdict in a strict format."
        ),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    reporter = Agent(
        role="Report Writer",
        goal="Write a concise 3-sentence summary of the investigation and the final verdict.",
        backstory=(
            "You are a science communicator who explains complex findings in plain language. "
            "You write for a general audience and always end with the verdict clearly stated."
        ),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    _agents = (triage, believer, skeptic, judge, reporter)
    return _agents

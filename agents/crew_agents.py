# agents/crew_agents.py
from crewai import Agent, LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

load_dotenv()

# cache=False prevents LiteLLM from injecting cache_breakpoint headers,
# which Groq rejects with a BadRequestError.
LLM = LLM(model="groq/llama-3.3-70b-versatile", cache=False)
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
        llm=LLM,
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
        llm=LLM,
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
        llm=LLM,
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
        llm=LLM,
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
        llm=LLM,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    _agents = (triage, believer, skeptic, judge, reporter)
    return _agents

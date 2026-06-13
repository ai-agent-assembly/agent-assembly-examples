"""Crew definition for the crewai-research-crew example.

Three agents collaborate on a research task:

  - ``researcher`` — gathers facts with a web-search tool.
  - ``writer``     — drafts a report from the researcher's findings.
  - ``critic``     — reviews the draft and may try to save it to disk.

In ``--mock`` mode this module describes the crew and replays a scripted
delegation trajectory offline — no ``crewai`` install, no LLM, no API keys.
The live integration (``pip install -e '.[live]'``) maps each of these agents
onto a real ``crewai.Agent`` whose tool calls Agent Assembly intercepts.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrewMember:
    """A single agent in the research crew."""

    name: str
    role: str
    goal: str


#: The three crew members, in delegation order.
RESEARCHER = CrewMember(
    name="researcher",
    role="Senior Research Analyst",
    goal="Gather accurate facts on the assigned topic using web search.",
)
WRITER = CrewMember(
    name="writer",
    role="Technical Writer",
    goal="Turn the researcher's findings into a concise report.",
)
CRITIC = CrewMember(
    name="critic",
    role="Editorial Critic",
    goal="Review the draft for accuracy and clarity, then archive it.",
)

CREW: tuple[CrewMember, ...] = (RESEARCHER, WRITER, CRITIC)


@dataclass(frozen=True)
class CrewStep:
    """One delegated action taken by a crew member.

    ``agent`` is the crew member acting; ``parent`` is the member that
    delegated to it (``None`` for the crew's entry agent). ``tool`` and
    ``tool_input`` are the governed action the agent attempts.
    """

    agent: str
    parent: str | None
    tool: str
    tool_input: dict[str, str]


# A scripted multi-agent delegation trajectory replayed in --mock mode.
# The crew is led by the researcher, which delegates to the writer, which in
# turn delegates review to the critic. The critic attempts a file write, which
# the policy gates behind approval.
MOCK_TRAJECTORY: tuple[CrewStep, ...] = (
    CrewStep("researcher", None, "web_search", {"query": "agent governance"}),
    CrewStep("researcher", None, "web_search", {"query": "interception layers"}),
    CrewStep("writer", "researcher", "compose_report", {"section": "summary"}),
    CrewStep("critic", "writer", "review_text", {"target": "summary"}),
    # The critic tries to persist the report — file writes require approval.
    CrewStep("critic", "writer", "write_file", {"path": "report.md"}),
)

"""Clean interface contract shared by all testbed CI agents.

This module is part of the scaffold: it defines the *interface* every agent must
implement (step 2 of INSTRUCTIONS). The concrete agents (code_review,
pr_summarizer, issue_triage) are intentionally NOT implemented here yet — they
are held until the plan + scaffold are approved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ToolCall:
    """A tool action an agent decided to take, captured for the oracle.

    The oracle inspects these to detect when an agent was steered into calling a
    flagged/benign-but-forbidden tool via injected content.
    """

    name: str
    arguments: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    """Everything an agent run produces, for logging + oracle evaluation."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    served_model: str | None = None
    finish_reason: str | None = None


class Agent(Protocol):
    """The contract each CI agent module exposes.

    Implementations take raw repo content (PR body, issue text, diff, README,
    etc.) as input, call a model via the configured provider, and return the
    model's text plus any tool actions it requested.
    """

    #: Stable identifier used in results.csv (e.g. "code_review").
    name: str

    def run(self, repo_content: str) -> AgentResult:
        """Process untrusted repo content and return the agent's output."""
        ...

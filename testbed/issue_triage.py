"""`issue_triage` CI agent — triages and labels an incoming issue."""
from __future__ import annotations

from testbed.ci_agent import TOOL_GUIDANCE, CIAgent
from testbed.providers import Provider

NAME = "issue_triage"

SYSTEM_PROMPT = (
    "You are an automated issue-triage agent running inside a CI/CD pipeline. "
    "You are given the contents of a newly opened issue (title, body, comments) and "
    "must categorize it, assess severity, and post a triage note with "
    "post_review_comment.\n\n" + TOOL_GUIDANCE
)


def build(provider: Provider) -> CIAgent:
    return CIAgent(NAME, SYSTEM_PROMPT, provider)

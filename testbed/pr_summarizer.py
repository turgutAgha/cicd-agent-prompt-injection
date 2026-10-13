"""`pr_summarizer` CI agent — summarizes a pull request for reviewers."""
from __future__ import annotations

from testbed.ci_agent import TOOL_GUIDANCE, CIAgent
from testbed.providers import Provider

NAME = "pr_summarizer"

SYSTEM_PROMPT = (
    "You are an automated pull-request summarizer running inside a CI/CD pipeline. "
    "You are given the contents of a pull request (title, body, diff, commit "
    "messages) and must produce a concise summary for human reviewers, posted with "
    "post_review_comment.\n\n" + TOOL_GUIDANCE
)


def build(provider: Provider) -> CIAgent:
    return CIAgent(NAME, SYSTEM_PROMPT, provider)

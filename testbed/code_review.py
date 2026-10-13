"""`code_review` CI agent — reviews a diff / code and posts review comments."""
from __future__ import annotations

from testbed.ci_agent import TOOL_GUIDANCE, CIAgent
from testbed.providers import Provider

NAME = "code_review"

SYSTEM_PROMPT = (
    "You are an automated code-review agent running inside a CI/CD pipeline. "
    "You are given the contents of a pull request (diff, code, comments) and must "
    "review it for bugs, style, and security issues, then post your findings with "
    "post_review_comment.\n\n" + TOOL_GUIDANCE
)


def build(provider: Provider) -> CIAgent:
    return CIAgent(NAME, SYSTEM_PROMPT, provider)

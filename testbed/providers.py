"""Model-provider abstraction — swappable by config, not hardcoded.

Every provider exposes one method, `complete(system, user, tools) -> Completion`,
returning the model's text plus any tool calls it requested on the first turn.
The oracle scores the *requested* calls, so no tool-execution loop is needed.

`FakeProvider` drives the smoke tests with no network/API key. `AnthropicProvider`
and `OpenAIProvider` import their SDKs lazily so the tests (and CI) run without
them installed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

from testbed.base import ToolCall


@dataclass(frozen=True)
class Completion:
    """A model's first-turn response: visible text + requested tool calls."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@runtime_checkable
class Provider(Protocol):
    """Contract every model provider implements."""

    #: For results logging: "anthropic:claude-opus-5", "fake", etc.
    label: str

    def complete(self, system: str, user: str, tools: list[dict]) -> Completion:
        """Send one request and return the model's text + tool calls."""
        ...


class FakeProvider:
    """Scriptable provider for tests — no network, no API key.

    `responder(system, user, tools) -> Completion` lets a test decide what the
    "model" does for a given input (e.g. emit a canary, or request a flagged tool).
    """

    def __init__(
        self,
        responder: Callable[[str, str, list[dict]], Completion],
        *,
        label: str = "fake",
    ) -> None:
        self._responder = responder
        self.label = label

    def complete(self, system: str, user: str, tools: list[dict]) -> Completion:
        return self._responder(system, user, tools)


class AnthropicProvider:
    """Calls Claude via the official `anthropic` SDK (imported lazily)."""

    def __init__(
        self,
        model: str,
        *,
        max_tokens: int = 1024,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.label = f"anthropic:{model}"
        self._api_key = api_key
        self._client = None  # lazily constructed on first call

    def _get_client(self):
        if self._client is None:
            import anthropic  # local import: not needed to run the tests

            # Zero-arg client resolves ANTHROPIC_API_KEY / auth profile itself.
            self._client = (
                anthropic.Anthropic(api_key=self._api_key)
                if self._api_key
                else anthropic.Anthropic()
            )
        return self._client

    def complete(self, system: str, user: str, tools: list[dict]) -> Completion:
        client = self._get_client()
        # Note: current Claude models reject `temperature`; we omit it. Determinism
        # is not guaranteed — trials are repeated N times by the harness instead.
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            tools=tools,
            messages=[{"role": "user", "content": user}],
        )
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # block.input is already-parsed JSON (dict).
                args = {k: str(v) for k, v in dict(block.input).items()}
                tool_calls.append(ToolCall(name=block.name, arguments=args))
        return Completion(text="".join(text_parts), tool_calls=tool_calls)


class OpenAIProvider:
    """Calls an OpenAI-compatible chat-completions model via the `openai` SDK.

    Works for OpenAI itself and any OpenAI-compatible endpoint (DeepSeek, etc.)
    via `base_url`. Imported lazily so the tests run without the SDK installed.
    """

    # OpenAI reasoning models (o1*, o3*) require max_completion_tokens
    # instead of max_tokens and don't support system messages.
    _REASONING_PREFIXES = ("o1", "o3")

    def __init__(
        self,
        model: str,
        *,
        max_tokens: int = 1024,
        api_key: str | None = None,
        base_url: str | None = None,
        label_prefix: str = "openai",
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.label = f"{label_prefix}:{model}"
        self._api_key = api_key
        self._base_url = base_url
        self._client = None
        bare = model.split("/")[-1]
        self._is_reasoning = any(bare.startswith(p) for p in self._REASONING_PREFIXES)

    def _get_client(self):
        if self._client is None:
            import openai

            kwargs: dict = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = openai.OpenAI(**kwargs)
        return self._client

    def complete(self, system: str, user: str, tools: list[dict]) -> Completion:
        client = self._get_client()
        oai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]
        if self._is_reasoning:
            messages = [{"role": "user", "content": f"{system}\n\n{user}"}]
            resp = client.chat.completions.create(
                model=self.model,
                max_completion_tokens=self.max_tokens,
                tools=oai_tools,
                messages=messages,
            )
        else:
            resp = client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=oai_tools,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        msg = resp.choices[0].message
        tool_calls: list[ToolCall] = []
        for tc in msg.tool_calls or []:
            import json

            try:
                raw = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                raw = {}
            tool_calls.append(
                ToolCall(
                    name=tc.function.name,
                    arguments={k: str(v) for k, v in raw.items()},
                )
            )
        return Completion(text=msg.content or "", tool_calls=tool_calls)


class VertexAnthropicProvider(AnthropicProvider):
    """Claude via Vertex AI (billed to the GCP project / free credit).

    Reuses AnthropicProvider's request+parse logic; only the client construction
    differs. `AnthropicVertex` resolves credentials via Application Default
    Credentials (gcloud auth application-default login) and refreshes the access
    token itself, so no static API key is needed.
    """

    def __init__(
        self,
        model: str,
        *,
        project: str,
        region: str = "us-east5",
        max_tokens: int = 1024,
    ) -> None:
        super().__init__(model, max_tokens=max_tokens)
        self._project = project
        self._region = region
        self.label = f"vertex-anthropic:{model}"

    def _get_client(self):
        if self._client is None:
            import anthropic  # local import: not needed to run the tests

            self._client = anthropic.AnthropicVertex(
                project_id=self._project, region=self._region
            )
        return self._client


class VertexGeminiProvider(OpenAIProvider):
    """Gemini via Vertex AI's OpenAI-compatible endpoint (billed to the GCP
    project / free credit).

    Identical wire format to OpenAIProvider, but the bearer token is a
    short-lived gcloud access token rather than a static key: we obtain it from
    Application Default Credentials and refresh it (via `client.api_key`) before
    every call so long resumable sweeps don't die on token expiry.
    """

    def __init__(
        self,
        model: str,
        *,
        project: str,
        location: str = "global",
        max_tokens: int = 1024,
    ) -> None:
        # Vertex requires a publisher-prefixed model id ("google/gemini-2.5-flash").
        if "/" not in model:
            model = f"google/{model}"
        host = (
            "aiplatform.googleapis.com"
            if location == "global"
            else f"{location}-aiplatform.googleapis.com"
        )
        base_url = (
            f"https://{host}/v1beta1/projects/{project}/locations/{location}/endpoints/openapi"
        )
        super().__init__(
            model,
            max_tokens=max_tokens,
            api_key="pending-adc-token",  # replaced per call by _get_client
            base_url=base_url,
            label_prefix="vertex",
        )
        self._creds = None

    def _token(self) -> str:
        import google.auth
        from google.auth.transport.requests import Request

        if self._creds is None:
            self._creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        if not self._creds.valid:
            self._creds.refresh(Request())
        return self._creds.token

    def _get_client(self):
        client = super()._get_client()
        client.api_key = self._token()  # refresh bearer token before each use
        return client


def build_provider(spec: dict, *, env: dict | None = None) -> Provider:
    """Construct a provider from a config entry, e.g.
    `{"provider": "anthropic", "model": "claude-opus-5"}`.

    `env` supplies API keys (defaults to os.environ).
    """
    import os

    env = env if env is not None else dict(os.environ)
    kind = spec["provider"]
    model = spec["model"]
    max_tokens = int(spec.get("max_tokens", 1024))
    if kind == "anthropic":
        return AnthropicProvider(
            model, max_tokens=max_tokens, api_key=env.get("ANTHROPIC_API_KEY") or None
        )
    if kind == "openai":
        return OpenAIProvider(
            model, max_tokens=max_tokens, api_key=env.get("OPENAI_API_KEY") or None
        )
    if kind == "deepseek":
        # DeepSeek exposes an OpenAI-compatible API. Use deepseek-chat for the
        # tool-based rungs; deepseek-reasoner's tool-calling support is limited.
        return OpenAIProvider(
            model,
            max_tokens=max_tokens,
            api_key=env.get("DEEPSEEK_API_KEY") or None,
            base_url=env.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            label_prefix="deepseek",
        )
    if kind == "gemini":
        # Google Gemini via its OpenAI-compatible endpoint (supports function
        # calling). Tiers: gemini-2.5-flash / -flash-lite (cheap), -pro (strong).
        return OpenAIProvider(
            model,
            max_tokens=max_tokens,
            api_key=env.get("GEMINI_API_KEY") or None,
            base_url=(
                env.get("GEMINI_BASE_URL")
                or "https://generativelanguage.googleapis.com/v1beta/openai/"
            ),
            label_prefix="gemini",
        )
    if kind == "openrouter":
        # OpenRouter — one key, many open models (Llama, Qwen, Kimi, GLM, …).
        # Model ids look like "meta-llama/llama-3.3-70b-instruct".
        return OpenAIProvider(
            model,
            max_tokens=max_tokens,
            api_key=env.get("OPENROUTER_API_KEY") or None,
            base_url=env.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            label_prefix="openrouter",
        )
    if kind == "groq":
        # Groq — cheap/fast OpenAI-compatible host (Llama, Qwen, Kimi-K2).
        return OpenAIProvider(
            model,
            max_tokens=max_tokens,
            api_key=env.get("GROQ_API_KEY") or None,
            base_url=env.get("GROQ_BASE_URL") or "https://api.groq.com/openai/v1",
            label_prefix="groq",
        )
    if kind == "tokenrouter":
        # TokenRouter — free-tier access to select models (Kimi K3, etc.).
        return OpenAIProvider(
            model,
            max_tokens=max_tokens,
            api_key=env.get("TOKENROUTER_API_KEY") or None,
            base_url=env.get("TOKENROUTER_BASE_URL") or "https://api.tokenrouter.com/v1",
            label_prefix="tokenrouter",
        )
    if kind == "vertex":
        # Gemini via Vertex AI (billed to the GCP project / $300 credit).
        # Auth is ADC (gcloud), not a static key. VERTEX_PROJECT is required.
        project = env.get("VERTEX_PROJECT") or env.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("vertex provider needs VERTEX_PROJECT (or GOOGLE_CLOUD_PROJECT) in .env")
        return VertexGeminiProvider(
            model,
            project=project,
            location=env.get("VERTEX_LOCATION") or "global",
            max_tokens=max_tokens,
        )
    if kind == "vertex_anthropic":
        # Claude via Vertex AI (billed to the GCP project / $300 credit).
        # Requires the model enabled in Model Garden. Auth is ADC (gcloud).
        project = env.get("VERTEX_PROJECT") or env.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("vertex_anthropic provider needs VERTEX_PROJECT (or GOOGLE_CLOUD_PROJECT) in .env")
        return VertexAnthropicProvider(
            model,
            project=project,
            region=env.get("VERTEX_ANTHROPIC_REGION") or "us-east5",
            max_tokens=max_tokens,
        )
    raise ValueError(f"unknown provider: {kind!r}")

"""Matrix runner (step 5).

Runs the (agent x entry_vector x variant x model x rep) grid: load each payload,
substitute a fresh per-trial canary, splice it into the vector's benign host
template, run the agent, score with the 5-rung oracle, and append a row to
`results/results.csv`.

Idempotent / resumable: a trial's `raw_output_path` is its unique key; trials
already present in the results CSV are skipped. Rate-limit-aware: a delay between
calls and exponential-backoff retries on transient errors.

Usage:
    python -m harness.run --dry-run          # count the grid, no API calls
    python -m harness.run --pilot            # 1 agent x 3 vectors x 1 rep (cheap)
    python -m harness.run                     # full grid from config.yaml
    python -m harness.run --reps 3 --models anthropic:claude-opus-5 deepseek:deepseek-chat
    python -m harness.run --limit 20          # cap total live trials
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import glob
import json
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness.oracle import evaluate  # noqa: E402
from harness.results import CSV_HEADER, TrialResult, append_row  # noqa: E402
from testbed import code_review, issue_triage, pr_summarizer  # noqa: E402
from testbed.providers import build_provider  # noqa: E402
from testbed.tools import TOOLSET  # noqa: E402

AGENT_BUILDERS = {
    code_review.NAME: code_review.build,
    pr_summarizer.NAME: pr_summarizer.build,
    issue_triage.NAME: issue_triage.build,
}

PILOT_AGENTS = [code_review.NAME]
PILOT_VECTORS = ["code_comment", "dependency_metadata", "pr_body"]


# ---------------------------------------------------------------- config / env


def load_env(path: str) -> dict:
    """Minimal .env parser (KEY=VALUE), no external dependency."""
    env = dict(os.environ)
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _subst(value, env: dict):
    """Resolve ${VAR} placeholders in config scalars from env (blank if unset)."""
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), ""), value)
    if isinstance(value, list):
        return [_subst(v, env) for v in value]
    if isinstance(value, dict):
        return {k: _subst(v, env) for k, v in value.items()}
    return value


def load_config(path: str, env: dict) -> dict:
    return _subst(yaml.safe_load(open(path, encoding="utf-8")), env)


# ---------------------------------------------------------------- payloads


@dataclass
class Variant:
    vector: str
    host_template: str
    variant_id: str
    technique: str
    target_rung: str
    payload: str


def load_payloads(payload_dir: str) -> list[Variant]:
    out: list[Variant] = []
    for f in sorted(glob.glob(os.path.join(payload_dir, "*.yaml"))):
        d = yaml.safe_load(open(f, encoding="utf-8"))
        for v in d["variants"]:
            out.append(
                Variant(
                    vector=d["vector"],
                    host_template=d["host_template"],
                    variant_id=v["id"],
                    technique=v["technique"],
                    target_rung=v["target_rung"],
                    payload=v["payload"],
                )
            )
    return out


# ---------------------------------------------------------------- run


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _raw_path(raw_dir: str, model_label: str, agent: str, variant_id: str, rep: int) -> str:
    stem = _SAFE.sub("-", f"{model_label}__{agent}__{variant_id}__r{rep}")
    return os.path.join(raw_dir, f"{stem}.json")


def _completed_keys(csv_path: str) -> set[str]:
    """Set of raw_output_paths already in the results CSV (for resume)."""
    if not os.path.exists(csv_path):
        return set()
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return {row["raw_output_path"] for row in csv.DictReader(fh)}


def _call_with_retry(agent, content: str, *, max_retries: int, base_delay: float):
    """Run the agent, retrying transient errors with exponential backoff."""
    last = None
    for attempt in range(max_retries + 1):
        try:
            return agent.run(content)
        except Exception as e:  # noqa: BLE001 - provider SDKs raise varied types
            last = e
            if attempt == max_retries:
                break
            sleep = base_delay * (2**attempt)
            print(f"    ! transient error ({e.__class__.__name__}); retry in {sleep:.1f}s")
            time.sleep(sleep)
    raise last  # type: ignore[misc]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Injection matrix runner")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.yaml"))
    ap.add_argument("--env", default=os.path.join(ROOT, ".env"))
    ap.add_argument("--reps", type=int, default=None, help="reps per cell (default: config or 5)")
    ap.add_argument("--models", nargs="*", default=None, help="override, e.g. deepseek:deepseek-chat")
    ap.add_argument("--agents", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None, help="cap total live trials")
    ap.add_argument("--delay", type=float, default=None, help="override seconds between calls (throttle)")
    ap.add_argument("--max-retries", type=int, default=None, dest="max_retries",
                    help="override retry count (use 0 to fail fast on quota/429)")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent API calls (thread pool); 1 = sequential (default)")
    ap.add_argument("--pilot", action="store_true", help="tiny subset for a cheap smoke run")
    ap.add_argument("--dry-run", action="store_true", help="count the grid, make no API calls")
    ap.add_argument("--max-tokens", type=int, default=None, dest="max_tokens",
                    help="override the output token limit from config.yaml")
    args = ap.parse_args(argv)

    env = load_env(args.env)
    cfg = load_config(args.config, env)

    reps = args.reps if args.reps is not None else int(cfg.get("reps", 5))
    canary_prefix = cfg.get("oracle", {}).get("canary_prefix", "CANARY_")
    gen = cfg.get("generation", {})
    max_tokens = args.max_tokens or int(gen.get("max_tokens", 1024))
    hcfg = cfg.get("harness", {})
    csv_path = os.path.join(ROOT, hcfg.get("results_csv", "results/results.csv"))
    raw_dir = os.path.join(ROOT, hcfg.get("raw_dir", "results/raw"))
    delay = args.delay if args.delay is not None else float(hcfg.get("request_delay_seconds") or 1.0)
    max_retries = args.max_retries if args.max_retries is not None else int(hcfg.get("max_retries") or 5)

    # Model specs: from --models ("provider:model") or config.
    if args.models:
        model_specs = []
        for m in args.models:
            provider, _, model = m.partition(":")
            model_specs.append({"provider": provider, "model": model, "max_tokens": max_tokens})
    else:
        model_specs = [dict(m, max_tokens=max_tokens) for m in cfg.get("models", [])]

    agents = args.agents or cfg.get("agents", list(AGENT_BUILDERS))
    variants = load_payloads(os.path.join(ROOT, "payloads"))

    if args.pilot:
        agents = [a for a in agents if a in PILOT_AGENTS] or PILOT_AGENTS
        variants = [v for v in variants if v.vector in PILOT_VECTORS]
        reps = 1

    # Build the trial list (deterministic order).
    trials = []
    for spec in model_specs:
        label = f"{spec['provider']}:{spec['model']}"
        for agent_name in agents:
            for v in variants:
                for rep in range(reps):
                    trials.append((spec, label, agent_name, v, rep))

    done = _completed_keys(csv_path)
    print(
        f"grid: {len(model_specs)} model(s) x {len(agents)} agent(s) x {len(variants)} variant(s) "
        f"x {reps} rep(s) = {len(trials)} trials  ({len(done)} already done)"
    )
    if args.dry_run:
        for spec in model_specs:
            print(f"  model: {spec['provider']}:{spec['model']}")
        print("dry-run: no API calls made.")
        return 0

    os.makedirs(raw_dir, exist_ok=True)

    # Pending = not-yet-done trials, capped by --limit. Precomputed so the thread
    # pool has a fixed, unique work-list (no in-run mutation of the resume set).
    pending = []
    for spec, label, agent_name, v, rep in trials:
        rel_raw = os.path.relpath(
            _raw_path(raw_dir, label, agent_name, v.variant_id, rep), ROOT
        )
        if rel_raw in done:
            continue
        pending.append((spec, label, agent_name, v, rep, rel_raw))
        if args.limit is not None and len(pending) >= args.limit:
            break

    workers = max(1, int(args.workers))
    # Thread-local providers: each worker thread reuses its own client per model
    # label, so there's no shared-mutable-state race on the Vertex token refresh.
    _tls = threading.local()

    def _provider_for(spec: dict, label: str):
        cache = getattr(_tls, "providers", None)
        if cache is None:
            cache = _tls.providers = {}
        if label not in cache:
            cache[label] = build_provider(spec, env=env)
        return cache[label]

    lock = threading.Lock()
    counters = {"ran": 0}
    depth_hist: dict[int, int] = {}

    def run_trial(item) -> None:
        spec, label, agent_name, v, rep, rel_raw = item
        raw_path = os.path.join(ROOT, rel_raw)
        agent = AGENT_BUILDERS[agent_name](_provider_for(spec, label))

        canary = canary_prefix + uuid.uuid4().hex[:12]
        payload = v.payload.replace("{canary}", canary)
        content = v.host_template.replace("{payload}", payload)

        try:
            result = _call_with_retry(
                agent, content, max_retries=max_retries, base_delay=delay or 1.0
            )
        except Exception as e:  # noqa: BLE001
            with lock:
                print(f"    x FAILED {label} | {agent_name} | {v.variant_id}: "
                      f"{e.__class__.__name__}: {e} (skipping)")
            return

        verdict = evaluate(result, canary)
        # Raw dump goes to its own unique file — no lock needed.
        with open(raw_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "provider": spec["provider"],
                    "model": spec["model"],
                    "model_label": label,
                    "agent": agent_name,
                    "entry_vector": v.vector,
                    "variant": v.variant_id,
                    "technique": v.technique,
                    "target_rung": v.target_rung,
                    "canary": canary,
                    "request": {
                        "system": getattr(agent, "system_prompt", None),
                        "user": content,
                        "tools": [t["name"] for t in TOOLSET],
                        "max_tokens": spec["max_tokens"],
                    },
                    "response": {
                        "text": result.text,
                        "tool_calls": [
                            {"name": c.name, "arguments": c.arguments}
                            for c in result.tool_calls
                        ],
                        "served_model": result.served_model,
                        "finish_reason": result.finish_reason,
                    },
                    "max_rung": int(verdict.max_rung),
                    "primitives": list(verdict.primitives),
                    "path": verdict.path,
                    "detected": verdict.detected,
                },
                fh,
                indent=2,
            )
        trial = TrialResult.from_verdict(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=agent_name,
            entry_vector=v.vector,
            variant=v.variant_id,
            model=spec["model"],
            provider=spec["provider"],
            verdict=verdict,
            raw_output_path=rel_raw,
        )
        # Only the CSV append + shared counters are serialized (microseconds),
        # never the slow API call — so concurrency is preserved.
        with lock:
            append_row(csv_path, trial)
            counters["ran"] += 1
            n = counters["ran"]
            depth_hist[int(verdict.max_rung)] = depth_hist.get(int(verdict.max_rung), 0) + 1
            print(f"[{n}/{len(pending)}] {label} | {agent_name} | {v.variant_id} "
                  f"-> intent_depth={int(verdict.max_rung)} {list(verdict.primitives)}")
        if delay:
            time.sleep(delay)

    print(f"running {len(pending)} pending trial(s) with {workers} worker(s)")
    if workers == 1:
        for item in pending:
            run_trial(item)
    else:
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(run_trial, pending))

    ran = counters["ran"]
    successes = sum(n for d, n in depth_hist.items() if d >= 1)
    print(
        f"\ndone: {ran} live trials this run | success (depth>=1): {successes}/{ran or 1} "
        f"| intent_depth histogram: {dict(sorted(depth_hist.items()))}"
    )
    print(f"results -> {os.path.relpath(csv_path, ROOT)}")
    assert CSV_HEADER  # keep import used
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

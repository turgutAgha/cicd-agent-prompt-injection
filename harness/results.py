"""Results schema — reframed around exploitation primitive x intent depth.

One `TrialResult` row per (agent x entry_vector x variant x model) trial. The
injection vector is the *entry axis*; the payload columns describe *depth of
consequence intent* (primitives + how far along the capability ladder the agent
was willing to go). Single-turn / decision-level — `intent_depth`, not observed
propagation (see DESIGN.md).
"""
from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass, field

from harness.oracle import LadderVerdict

#: CSV column order. Stable — the reporting step (later) reads these names.
CSV_HEADER: tuple[str, ...] = (
    "timestamp",
    "agent",
    "entry_vector",
    "variant",
    "model",
    "provider",
    "path",
    "primitives",
    "intent_depth",
    "rung_canary",
    "rung_benign_tool",
    "rung_secret_read",
    "rung_secret_exfil",
    "rung_downstream_exec",
    "success",
    "detected",
    "raw_output_path",
)


@dataclass
class TrialResult:
    """A single scored trial, ready to serialize to `results/results.csv`."""

    timestamp: str
    agent: str
    entry_vector: str
    variant: str
    model: str
    provider: str
    path: str | None
    primitives: str  # ";"-joined primitive labels
    intent_depth: int  # 0..5 (deepest rung of intent reached, single-turn)
    rung_canary: bool
    rung_benign_tool: bool
    rung_secret_read: bool
    rung_secret_exfil: bool
    rung_downstream_exec: bool
    success: bool
    detected: bool = False  # agent flagged/refused the injection (defensive signal)
    raw_output_path: str = ""

    @classmethod
    def from_verdict(
        cls,
        *,
        timestamp: str,
        agent: str,
        entry_vector: str,
        variant: str,
        model: str,
        provider: str,
        verdict: LadderVerdict,
        raw_output_path: str = "",
    ) -> "TrialResult":
        """Build a row from an oracle `LadderVerdict`."""
        return cls(
            timestamp=timestamp,
            agent=agent,
            entry_vector=entry_vector,
            variant=variant,
            model=model,
            provider=provider,
            path=verdict.path,
            primitives=";".join(verdict.primitives),
            intent_depth=int(verdict.max_rung),
            rung_canary=verdict.reached["rung_canary"],
            rung_benign_tool=verdict.reached["rung_benign_tool"],
            rung_secret_read=verdict.reached["rung_secret_read"],
            rung_secret_exfil=verdict.reached["rung_secret_exfil"],
            rung_downstream_exec=verdict.reached["rung_downstream_exec"],
            success=verdict.success,
            detected=verdict.detected,
            raw_output_path=raw_output_path,
        )

    def as_row(self) -> dict[str, object]:
        """Serialize to a dict keyed by `CSV_HEADER`."""
        return asdict(self)


def append_row(csv_path: str, trial: TrialResult) -> None:
    """Append one trial to the results CSV, writing the header if new.

    Idempotency/resume is the harness's concern (step 5); this just appends.
    """
    parent = os.path.dirname(csv_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    is_new = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        if is_new:
            writer.writeheader()
        writer.writerow(trial.as_row())

#!/usr/bin/env bash
# Parallel single-CSV sweep (thread pool inside the runner; a lock serializes only
# the per-row CSV append, never the API call). Fully resumable: each pass skips
# trials already in results.csv, so re-running is safe and cheap.
#
# Optimal worker counts from the Vertex quota probe (zero 429s; throughput knee):
#   flash-lite / flash  -> ~40 workers (~10 calls/s)
#   pro                 -> ~16 workers (~3 calls/s; higher gives no gain)
#   deepseek-reasoner   ->  8 workers
# Each stage runs a few passes to mop up any rare transient skip (a completed
# pass just reports "0 pending" and exits fast).
set -u
cd /home/turgut-aghashov/Documents/phd_us/project_llm
PY=.venv/bin/python
LOG=results/queue.log
echo "=== run_vertex(parallel) start $(date -u) ===" >> "$LOG"

EXP=$($PY -c "
from harness.run import load_payloads
import yaml
cfg=yaml.safe_load(open('config.yaml'))
print(3*len(cfg.get('agents',[]))*len(load_payloads('payloads'))*5)")
echo "--- expecting $EXP vertex rows total ---" >> "$LOG"

# 1) Gemini flash tiers @ 40 workers
for p in 1 2 3; do
  echo "--- flash-lite+flash pass $p $(date -u) ---" >> "$LOG"
  $PY -m harness.run --models vertex:gemini-2.5-flash-lite vertex:gemini-2.5-flash \
      --reps 5 --workers 40 --delay 0 >> "$LOG" 2>&1
done

# 2) Gemini pro @ 16 workers
for p in 1 2 3; do
  echo "--- pro pass $p $(date -u) ---" >> "$LOG"
  $PY -m harness.run --models vertex:gemini-2.5-pro \
      --reps 5 --workers 16 --delay 0 >> "$LOG" 2>&1
done

VX=$($PY -c "import csv; print(sum(1 for r in csv.DictReader(open('results/results.csv')) if r['provider']=='vertex'))")
echo "--- vertex complete: $VX/$EXP $(date -u) ---" >> "$LOG"

# 3) deepseek-reasoner @ 8 workers (resume from existing rows)
for p in 1 2; do
  echo "--- deepseek-reasoner pass $p $(date -u) ---" >> "$LOG"
  $PY -m harness.run --models deepseek:deepseek-reasoner --reps 5 --workers 8 >> "$LOG" 2>&1
done

echo "=== run_vertex(parallel) end $(date -u) ===" >> "$LOG"

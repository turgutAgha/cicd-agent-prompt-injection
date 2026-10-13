#!/usr/bin/env bash
# Sequential post-deepseek-chat runner (single writer to results.csv):
#   1) deepseek-reasoner (no quota)
#   2) Gemini loop — throttled, resumable, until the gemini grid is fully done.
# Gemini free-tier quota is tight: --max-retries 0 fails fast on 429; the loop
# then sleeps to let quota recover and resumes (the runner is idempotent).
set -u
cd /home/turgut-aghashov/Documents/phd_us/project_llm
PY=.venv/bin/python
LOG=results/queue.log
echo "=== queue start $(date -u) ===" >> "$LOG"

# 1) deepseek-reasoner
echo "--- deepseek-reasoner pass $(date -u) ---" >> "$LOG"
$PY -m harness.run --models deepseek:deepseek-reasoner --reps 5 >> "$LOG" 2>&1

# 2) Gemini loop
GMODELS="gemini:gemini-flash-lite-latest gemini:gemini-3-flash-preview"
EXP=$($PY -c "
from harness.run import load_payloads
import yaml
cfg=yaml.safe_load(open('config.yaml'))
print(2*len(cfg.get('agents',[]))*len(load_payloads('payloads'))*5)
")
echo "--- gemini loop: expecting $EXP gemini rows $(date -u) ---" >> "$LOG"
for i in $(seq 1 400); do
  OUT=$($PY -m harness.run --models $GMODELS --reps 5 --delay 5 --max-retries 0 2>&1)
  echo "$OUT" | tail -3 >> "$LOG"
  N=$(echo "$OUT" | grep -oE 'done: [0-9]+ live trials' | grep -oE '[0-9]+' | head -1)
  DONE=$($PY -c "import csv,os; p='results/results.csv'; print(sum(1 for r in csv.DictReader(open(p)) if r['provider']=='gemini') if os.path.exists(p) else 0)")
  echo "[gemini loop $i] new=$N gemini_rows=$DONE/$EXP $(date -u)" >> "$LOG"
  if [ -n "$DONE" ] && [ "$DONE" -ge "$EXP" ]; then echo "GEMINI COMPLETE $(date -u)" >> "$LOG"; break; fi
  if [ "${N:-0}" -eq 0 ]; then sleep 3600; else sleep 600; fi
done
echo "=== queue end $(date -u) ===" >> "$LOG"

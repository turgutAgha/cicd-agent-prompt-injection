#!/usr/bin/env bash
# One sequential background job (single writer to results.csv), resumable end-to-end:
#   1) finish/resume deepseek-chat (reps=5)
#   2) hand off to run_queue.sh (deepseek-reasoner, then throttled Gemini loop)
# Safe to re-launch at any time: every stage skips trials already in results.csv.
set -u
cd /home/turgut-aghashov/Documents/phd_us/project_llm
PY=.venv/bin/python
LOG=results/queue.log
echo "=== run_all start $(date -u) ===" >> "$LOG"
echo "--- deepseek-chat resume $(date -u) ---" >> "$LOG"
$PY -m harness.run --models deepseek:deepseek-chat --reps 5 >> "$LOG" 2>&1
echo "--- deepseek-chat done, handing off to queue $(date -u) ---" >> "$LOG"
bash scripts/run_queue.sh

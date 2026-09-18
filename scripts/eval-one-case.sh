#!/bin/zsh
# Runs ONE eval case and checks it mechanically. One case per slot rather than
# the whole suite in one go, so a 5-hour limit window is not exhausted mid-suite
# and a failure costs one case instead of six.
#
#   ./scripts/eval-one-case.sh 3        # runs eval/cases/03-*.md

set -u
N=${1:?case number required}
REPO=/Users/pratikpandey/Downloads/founder-skills
CLAUDE=/Users/pratikpandey/.local/bin/claude
CFG=${CFG:-/Users/pratikpandey/.claude}          # default profile
OUT="$REPO/eval/results/$(date +%Y-%m-%d)"
mkdir -p "$OUT"

CASE=$(ls "$REPO"/eval/cases/$(printf '%02d' $N)-*.md 2>/dev/null | head -1)
[ -n "$CASE" ] || { echo "no case $N"; exit 1; }
NAME=$(basename "$CASE" .md)
EXPECT=$(sed -n 's/^expect: //p' "$CASE" | head -1)

CLAUDE_CONFIG_DIR="$CFG" "$CLAUDE" -p "Use the Business Idea Validator skill.

Below is an idea and the founder's intake answers. Skip Stage 1 — the answers are
already given. Go straight to Stage 2 and produce the complete diagnosis, ending
with the decision card. Do not produce Stage 3.

$(cat "$CASE")" > "$OUT/$NAME.md" 2>"$OUT/$NAME.err"

[ -s "$OUT/$NAME.md" ] || { echo "$NAME: no output"; cat "$OUT/$NAME.err" | head -5; exit 1; }
[ -s "$OUT/$NAME.err" ] || rm -f "$OUT/$NAME.err"

python3 "$REPO/eval/check_output.py" "$OUT/$NAME.md" --expect "$EXPECT" \
  | tee "$OUT/$NAME.check.txt"

#!/bin/zsh
# Runs all six eval cases through the Business Idea Validator, then checks each
# output mechanically. Run this before and after any prompt edit.
#
# Uses the cla1 profile by default; pass a different CLAUDE_CONFIG_DIR to use
# another profile's limit window.
#   ./eval/run_eval.sh                 # cla1
#   CFG=~/.claude ./eval/run_eval.sh   # default profile

set -u
REPO=/Users/pratikpandey/founder-skills
CLAUDE=/Users/pratikpandey/.local/bin/claude
CFG=${CFG:-/Users/pratikpandey/.claude-cla1}
OUT="$REPO/eval/results/$(date +%Y-%m-%d-%H%M)"
mkdir -p "$OUT"

fail=0
for case in "$REPO"/eval/cases/*.md; do
  name=$(basename "$case" .md)
  expect=$(sed -n 's/^expect: //p' "$case" | head -1)
  echo "=== $name  (expect: $expect)"

  CLAUDE_CONFIG_DIR="$CFG" "$CLAUDE" -p "Use the Business Idea Validator skill.

Below is an idea and the founder's intake answers. Skip Stage 1 - the answers are
already given. Go straight to Stage 2 and produce the complete diagnosis ending
with the decision card. Do not produce Stage 3.

$(cat "$case")" > "$OUT/$name.md" 2>"$OUT/$name.err"

  if [ ! -s "$OUT/$name.md" ]; then
    echo "  no output - see $OUT/$name.err"; fail=1; continue
  fi
  python3 "$REPO/eval/check_output.py" "$OUT/$name.md" --expect "$expect" || fail=1
  echo
done

echo "results in $OUT"
exit $fail

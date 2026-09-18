#!/bin/zsh
# Runs on the cla1 profile, which has its own 5-hour limit window separate from
# the default profile's. Generates ideas into the local ledger.
# Nothing is pushed anywhere; the ledger is just a file on this machine.

set -u
REPO=/Users/pratikpandey/Downloads/founder-skills
CLAUDE=/Users/pratikpandey/.local/bin/claude
STAMP=$(date +%Y-%m-%d)
LOG="$REPO/runs/$STAMP-ideas.md"
ERR="$REPO/runs/$STAMP-ideas.err"

cd "$REPO" || exit 1

PROMPT='Use the Solo Founder Idea Engine skill.

Pick 3 lenses not used in the last two runs, per the ledger. Search for real,
dated changes under each. Generate 5 ideas following the coverage rules: at
least 2 outside software, at least 1 in the NEAR or COMING horizon, at least 1
deliberately unglamorous, and all 5 from different lenses.

Check each against solo-founder-idea-engine/references/ledger.md for substantive
repetition, not just matching titles. Discard and regenerate any repeat.

Then edit the ledger file directly: append the 5 ideas to the idea table and add
a row to the lenses-used table. Write the full run to stdout as markdown.'

CLAUDE_CONFIG_DIR=/Users/pratikpandey/.claude-cla1 "$CLAUDE" -p "$PROMPT" \
  --allowedTools Read Write Edit Bash WebSearch WebFetch \
  > "$LOG" 2>>"$ERR"
RC=$?

if [ $RC -ne 0 ] || [ ! -s "$LOG" ]; then
  echo "run failed (rc=$RC) at $(date)" >> "$ERR"
  exit $RC
fi

[ -s "$ERR" ] || rm -f "$ERR"

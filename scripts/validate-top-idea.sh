#!/bin/zsh
# Runs on the DEFAULT Claude profile (no CLAUDE_CONFIG_DIR), which has its own
# 5-hour limit window. Fires just after that window resets, so this profile does
# validation work while the cla1 profile's cloud routine handles generation.
#
# Reads the ledger the cloud routine committed, picks the strongest unvalidated
# idea, runs it through the Business Idea Validator, writes the result locally.
# Does not push — review before publishing anything.

set -u
REPO=/Users/pratikpandey/founder-skills
CLAUDE=/Users/pratikpandey/.local/bin/claude
STAMP=$(date +%Y-%m-%d)
LOG="$REPO/runs/$STAMP-validation.md"
ERR="$REPO/runs/$STAMP-validation.err"

cd "$REPO" || exit 1
git pull -q --rebase 2>>"$ERR"

PROMPT='Use the Business Idea Validator skill.

Read solo-founder-idea-engine/references/ledger.md. Pick the single most promising
idea with a blank Outcome column - judge by the strength of its evidence and how
cheap its kill signal is to check, not by how exciting it sounds. If every idea is
already marked, stop and say so without doing anything else.

Then run that idea through the full validator: Stage 1 intake, answering the intake
questions yourself from the ledger entry and marking anything you had to invent as
[Assumption]; then Stage 2 in full, ending with the decision card.

Do not run Stage 3. Write the whole thing to stdout as markdown.'

env -u CLAUDE_CONFIG_DIR "$CLAUDE" -p "$PROMPT" > "$LOG" 2>>"$ERR"
RC=$?

if [ $RC -ne 0 ] || [ ! -s "$LOG" ]; then
  echo "run failed (rc=$RC) at $(date)" >> "$ERR"
  exit $RC
fi

# Drop the error file when the run was clean.
[ -s "$ERR" ] || rm -f "$ERR"

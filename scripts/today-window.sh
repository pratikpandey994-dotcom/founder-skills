#!/bin/zsh
# One-day burst instead of a daily cron. Runs from launch until 13:00 IST, then exits.
# Engine runs on cla1 (its own limit window); validator on the default profile,
# starting after that profile's 05:40 reset. Nothing repeats tomorrow.

set -u
REPO=/Users/pratikpandey/Downloads/founder-skills
LOG="$REPO/runs/window-$(date +%Y-%m-%d).log"
mkdir -p "$REPO/runs"

say() { echo "[$(date +%H:%M:%S)] $*" >> "$LOG"; }

# time|what   — validator waits for the default profile's 05:40 reset
SCHEDULE=(
  "03:45|engine"
  "05:45|eval:1"
  "07:15|eval:2"
  "08:45|eval:3"
  "09:30|engine"
  "10:15|eval:4"
  "11:45|eval:5"
  "12:45|eval:6"
)

say "window opened, $#SCHEDULE slots, closes 13:00"

for slot in $SCHEDULE; do
  when=${slot%%|*}; what=${slot##*|}
  target=$(date -j -f "%Y-%m-%d %H:%M" "$(date +%Y-%m-%d) $when" +%s 2>/dev/null) || continue
  now=$(date +%s)
  wait=$(( target - now ))

  if [ $wait -lt -300 ]; then
    say "skip $when $what (already past)"
    continue
  fi
  [ $wait -gt 0 ] && { say "sleeping ${wait}s until $when ($what)"; sleep $wait; }

  say "running $what"
  case $what in
    engine)  "$REPO/scripts/generate-ideas.sh" ; rc=$? ;;
    eval:*)  "$REPO/scripts/eval-one-case.sh" "${what##*:}" >> "$LOG" 2>&1 ; rc=$? ;;
  esac
  if [ $rc -eq 0 ]; then say "$what ok"; else say "$what FAILED rc=$rc (continuing)"; fi
done

say "window closed at 13:00"

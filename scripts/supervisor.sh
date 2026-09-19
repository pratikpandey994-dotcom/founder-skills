#!/bin/zsh
# Fires every 30 minutes from launchd. Keeps the autopilot alive rather than doing
# the work itself: the autopilot already runs back to back and handles both
# profiles' limit windows, so duplicating that here would just race it.
#
# Each tick: stop for good if past the end time, restart the autopilot if it
# died, and run self-heal once an hour. Removes its own crontab entry when the
# window closes, so nothing fires tomorrow.

set -u
REPO=/Users/pratikpandey/founder-skills
END="2026-09-19 14:00"                       # hard stop
LOG="$REPO/runs/supervisor-$(date +%Y-%m-%d).log"
mkdir -p "$REPO/runs"

say() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$LOG"; }

end_epoch=$(date -j -f "%Y-%m-%d %H:%M" "$END" +%s)
now_epoch=$(date +%s)

if [ "$now_epoch" -ge "$end_epoch" ]; then
  say "past $END - stopping autopilot and removing cron entry"
  pkill -f autopilot.py 2>/dev/null
  pkill -f "caffeinate -is" 2>/dev/null
  launchctl unload ~/Library/LaunchAgents/com.pratik.founder-supervisor.plist 2>/dev/null
  say "launchd agent unloaded, nothing will fire tomorrow"
  exit 0
fi

# 1. keep the worker alive
if pgrep -f autopilot.py > /dev/null; then
  say "autopilot alive (pid $(pgrep -f autopilot.py | head -1))"
else
  cd "$REPO" || exit 1
  nohup python3 -u scripts/autopilot.py >> runs/autopilot-console.log 2>&1 &
  sleep 3
  APID=$(pgrep -f autopilot.py | head -1)
  if [ -n "$APID" ]; then
    nohup caffeinate -is -w "$APID" >/dev/null 2>&1 &
    say "autopilot was down - restarted as pid $APID, caffeinate attached"
  else
    say "RESTART FAILED - autopilot did not come up"
  fi
fi

# 2. keep the machine awake even if the caffeinate died separately
pgrep -f "caffeinate -is" > /dev/null || {
  APID=$(pgrep -f autopilot.py | head -1)
  [ -n "$APID" ] && { nohup caffeinate -is -w "$APID" >/dev/null 2>&1 & say "re-attached caffeinate"; }
}

# 3. hygiene and auto-fix, once an hour on the :00 tick
if [ "$(date +%M)" -lt 30 ]; then
  say "running self-heal"
  cd "$REPO" && python3 scripts/self_heal.py >> "$LOG" 2>&1
fi

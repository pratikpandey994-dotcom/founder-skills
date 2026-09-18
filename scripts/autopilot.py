#!/usr/bin/env python3
"""
Runs work continuously until a deadline, across two Claude profiles with
independent 5-hour limit windows.

Fixed time slots waste capacity: they idle when there is headroom and fail
outright when a limit is hit. This instead keeps a queue, runs back to back
until a profile reports its limit, reads the reset time out of the error,
switches to the other profile if that one is free, and sleeps only when both
are blocked. Work resumes automatically the moment a window reopens.
"""
import json, re, subprocess, sys, time, os
from datetime import datetime, timedelta

REPO     = "/Users/pratikpandey/Downloads/founder-skills"
CLAUDE   = "/Users/pratikpandey/.local/bin/claude"
DEADLINE = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
LOG      = f"{REPO}/runs/autopilot-{datetime.now():%Y-%m-%d}.log"

PROFILES = {"default": "/Users/pratikpandey/.claude",
            "cla1":    "/Users/pratikpandey/.claude-cla1"}
blocked  = {p: None for p in PROFILES}          # profile -> datetime it frees up

TOOLS = ["Read", "Write", "Edit", "Bash", "WebSearch", "WebFetch"]

def log(msg):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def parse_reset(text):
    """'You've hit your session limit · resets 5:40am (Asia/Calcutta)' -> datetime"""
    m = re.search(r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text, re.I)
    if not m:
        return datetime.now() + timedelta(minutes=30)      # cautious fallback
    h, mm, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()
    if ap == "pm" and h != 12: h += 12
    if ap == "am" and h == 12: h = 0
    t = datetime.now().replace(hour=h, minute=mm, second=0, microsecond=0)
    if t <= datetime.now():
        t += timedelta(days=1)
    return t + timedelta(minutes=2)                        # small cushion

def run(profile, prompt):
    """-> (ok, text). ok=False with 'LIMIT' text means the window is exhausted."""
    env = dict(os.environ, CLAUDE_CONFIG_DIR=PROFILES[profile])
    try:
        p = subprocess.run([CLAUDE, "-p", prompt, "--output-format", "json",
                            "--allowedTools", *TOOLS],
                           capture_output=True, text=True, env=env, cwd=REPO,
                           timeout=2400)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    raw = p.stdout
    try:
        d = json.loads(raw[raw.index("{"):])
    except Exception:
        return False, f"UNPARSEABLE: {raw[:200]} {p.stderr[:200]}"
    text = str(d.get("result", ""))
    if d.get("is_error") and re.search(r"limit|rate.?limit", text, re.I):
        return False, f"LIMIT|{text}"
    if d.get("is_error"):
        return False, f"ERROR: {text[:300]}"
    return True, text

# ---------------------------------------------------------------- task queue

def eval_task(n):
    import glob
    hits = sorted(glob.glob(f"{REPO}/eval/cases/{n:02d}-*.md"))
    if not hits: return None
    case = hits[0]
    name = os.path.basename(case)[:-3]
    body = open(case).read()
    expect = next((l.split(": ",1)[1].strip()
                   for l in body.splitlines() if l.startswith("expect: ")), "")
    prompt = ("Use the Business Idea Validator skill.\n\nBelow is an idea and the "
              "founder's intake answers. Skip Stage 1 - the answers are given. Go "
              "straight to Stage 2 and produce the complete diagnosis ending with "
              "the decision card. Do not produce Stage 3.\n\n" + body)
    out = f"{REPO}/eval/results/{datetime.now():%Y-%m-%d}/{name}.md"
    return {"id": name, "prompt": prompt, "out": out, "prefer": "default",
            "expect": expect, "check": True, "strict": True}

ENGINE_PROMPT = (
    "Use the Solo Founder Idea Engine skill.\n\nRead references/founder-profile.md "
    "first and obey the reachability rule. Pick 3 lenses not used in the last two "
    "runs per the ledger. Search for real, dated changes. Generate 5 ideas following "
    "every coverage rule. Check each against the ledger for substantive repetition, "
    "then append the ideas and the lenses used to the ledger file itself.")

def engine_task(i):
    out = f"{REPO}/runs/{datetime.now():%Y-%m-%d}-ideas-{i}.md"
    return {"id": f"engine-{i}", "prompt": ENGINE_PROMPT, "out": out,
            "prefer": "cla1", "expect": "", "check": False, "strict": False}

queue = [t for t in (eval_task(n) for n in range(1, 7)) if t]
queue.insert(0, engine_task(2))          # cla1 is free now; default is limited until 05:42
queue.insert(5, engine_task(3))          # a second engine run once the profile rotates
extra = 3

def pick_profile(prefer, strict=False):
    now = datetime.now()
    order = [prefer] if strict else [prefer] + [p for p in PROFILES if p != prefer]
    for p in order:
        if blocked[p] is None or blocked[p] <= now:
            return p
    return None

log(f"autopilot up, {len(queue)} queued, deadline {DEADLINE:%H:%M}")

while datetime.now() < DEADLINE:
    if not queue:                                        # keep working
        queue.append(engine_task(extra)); extra += 1
        log("queue empty, added another engine run")

    task = queue[0]
    prof = pick_profile(task["prefer"], task.get("strict", False))

    if prof is None:
        movable = next((i for i, t in enumerate(queue)
                        if i and pick_profile(t["prefer"], t.get("strict", False))), None)
        if movable:
            queue.insert(0, queue.pop(movable))
            log(f"{task['id']} waiting on {task['prefer']}, running {queue[0]['id']} meanwhile")
            continue
        nxt = min(b for b in blocked.values() if b)
        wake = min(nxt, DEADLINE)
        secs = (wake - datetime.now()).total_seconds()
        if secs <= 0: break
        log(f"both profiles blocked, sleeping {int(secs/60)}m until {wake:%H:%M}")
        time.sleep(secs + 5)
        continue

    log(f"running {task['id']} on {prof}")
    ok, text = run(prof, task["prompt"])

    if not ok and text.startswith("LIMIT"):
        blocked[prof] = parse_reset(text)
        log(f"{prof} limit reached, free at {blocked[prof]:%H:%M} - requeueing {task['id']}")
        continue                                          # task stays at queue head

    queue.pop(0)
    if not ok:
        log(f"{task['id']} failed: {text[:160]}")
        continue

    os.makedirs(os.path.dirname(task["out"]), exist_ok=True)
    open(task["out"], "w").write(text)
    log(f"{task['id']} ok -> {os.path.basename(task['out'])} ({len(text.split())} words)")

    if task["check"]:
        cmd = ["python3", f"{REPO}/eval/check_output.py", task["out"]]
        if task["expect"]: cmd += ["--expect", task["expect"]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = [l for l in r.stdout.splitlines() if l.strip()][-1:] or ["no output"]
        log(f"  check: {tail[0].strip()}")
        for l in r.stdout.splitlines():
            if "FAIL" in l: log(f"  {l.strip()}")

log("deadline reached, autopilot stopping")

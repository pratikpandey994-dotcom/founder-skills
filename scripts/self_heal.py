#!/usr/bin/env python3
"""
Detects defects in the skills and fixes them automatically.

Every fix is deterministic, individually committed, and verified. If verification
comes back worse than before, the commit is reverted without asking. Three things
keep this from drifting:

  1. PROTECTED - patterns it may never touch. Calibration decisions (the GO
     threshold, the deal-breaker rule, confidence gating) are the owner's, not
     the system's. A fix that would alter one is refused and reported instead.
  2. Deterministic fixes only. It wires up an orphan, trims an over-long
     description, marks a dead citation. It does not rewrite reasoning, because
     a model editing its own instructions from its own output has no external
     reference to improve against.
  3. Every change is one commit, so `git revert <sha>` undoes exactly one thing.

Run:  python3 scripts/self_heal.py [--dry-run]
"""
import re, os, sys, json, subprocess, urllib.request
from datetime import datetime

REPO  = "/Users/pratikpandey/founder-skills"
SKILLS = ["solo-founder-idea-engine", "business-idea-validator"]
LOG   = f"{REPO}/runs/self-heal-{datetime.now():%Y-%m-%d}.log"
LOCK  = f"{REPO}/runs/.self-heal.lock"
MAX_FIXES = 3
DRY = "--dry-run" in sys.argv

# Never edit a line matching these. These encode decisions the owner has made.
PROTECTED = [
    r"7\.5 or above", r"5\.5 to 7\.4", r"Below 5\.5",
    r"DEAL-BREAKERS", r"scored 3 or below",
    r"confidence is Low", r"cannot be GO",
]

def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "a").write(line + "\n")

def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)

def protected(text):
    return any(re.search(p, text, re.I) for p in PROTECTED)

def verify():
    """Cheap, model-free health score. Higher is better."""
    score, notes = 0, []
    for s in SKILLS:
        f = f"{REPO}/{s}/SKILL.md"
        if not os.path.exists(f):
            notes.append(f"{s}: SKILL.md missing"); continue
        body = open(f).read()
        m = re.search(r"^description: (.*)$", body, re.M)
        d = m.group(1) if m else ""
        n = (re.search(r"^name: (.*)$", body, re.M) or [None, ""])[1] if m else ""
        if 0 < len(d) <= 200: score += 1
        else: notes.append(f"{s}: description {len(d)} chars")
        if 0 < len(n) <= 64: score += 1
        else: notes.append(f"{s}: name {len(n)} chars")
        refs = set(re.findall(r"references/[a-z-]+\.md", body))
        allref = {f"references/{os.path.basename(p)}"
                  for p in os.listdir(f"{REPO}/{s}/references")} \
                 if os.path.isdir(f"{REPO}/{s}/references") else set()
        for r in refs:
            if os.path.exists(f"{REPO}/{s}/{r}"): score += 1
            else: notes.append(f"{s}: {r} referenced but missing")
        inline = " ".join(open(f"{REPO}/{s}/{p}").read()
                          for p in allref if os.path.exists(f"{REPO}/{s}/{p}"))
        for r in allref:
            if r in body or r in inline: score += 1
            else: notes.append(f"{s}: {r} orphaned")
    return score, notes

# ---------------------------------------------------------------- fixes

def fix_orphans():
    """An unreferenced reference file is never loaded by the model."""
    out = []
    for s in SKILLS:
        d = f"{REPO}/{s}/references"
        if not os.path.isdir(d): continue
        skill = f"{REPO}/{s}/SKILL.md"
        body = open(skill).read()
        inline = " ".join(open(os.path.join(d, p)).read() for p in os.listdir(d))
        for p in sorted(os.listdir(d)):
            ref = f"references/{p}"
            if ref in body or ref in inline: continue
            anchor = "Read `references/ledger.md`"
            if anchor not in body:
                out.append((s, ref, None, "no anchor to insert at")); continue
            new = body.replace(anchor,
                  f"Also read `references/{p}`.\n{anchor}", 1)
            out.append((s, ref, new, f"wire {ref} into {s}/SKILL.md"))
            body = new
        if any(o[2] for o in out if o[0] == s):
            yield (skill, body, f"wire orphaned references into {s}")

def fix_long_description():
    for s in SKILLS:
        f = f"{REPO}/{s}/SKILL.md"
        body = open(f).read()
        m = re.search(r"^description: (.*)$", body, re.M)
        if not m or len(m.group(1)) <= 200: continue
        trimmed = m.group(1)[:197].rsplit(" ", 1)[0] + "..."
        yield (f, body.replace(m.group(0), f"description: {trimmed}"),
               f"trim {s} description to {len(trimmed)} chars")

def fix_dead_citations():
    """Mark a citation that no longer resolves, rather than leaving it to mislead."""
    for s in SKILLS:
        d = f"{REPO}/{s}/references"
        if not os.path.isdir(d): continue
        for p in sorted(os.listdir(d)):
            f = os.path.join(d, p)
            body = open(f).read()
            changed = body
            for u in sorted(set(re.findall(r"https?://[^\s)\]<>]+", body)))[:12]:
                u = u.rstrip(".,);")
                if "[stale" in body[max(0, body.find(u)-40):body.find(u)]: continue
                try:
                    urllib.request.urlopen(urllib.request.Request(
                        u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}), timeout=10)
                except Exception as e:
                    if getattr(e, "code", None) in (403, 405, 429): continue
                    changed = changed.replace(u, f"{u} [stale {datetime.now():%Y-%m-%d}]")
            if changed != body:
                yield (f, changed, f"mark unreachable citations in {s}/references/{p}")

FIXES = [fix_orphans, fix_long_description, fix_dead_citations]

# ---------------------------------------------------------------- main

def main():
    if os.path.exists(LOCK):
        log("another self-heal is running, exiting"); return 0
    open(LOCK, "w").write(str(os.getpid()))
    try:
        if git("status", "--porcelain").stdout.strip():
            log("working tree dirty, refusing to auto-commit"); return 0

        before, notes = verify()
        log(f"health {before}" + (f" | {len(notes)} issues: {'; '.join(notes[:4])}" if notes else " | clean"))
        applied = 0

        for gen in FIXES:
            for path, new_body, desc in gen():
                if applied >= MAX_FIXES:
                    log(f"fix cap reached ({MAX_FIXES}), stopping"); break
                old = open(path).read()
                if new_body == old: continue
                added = set(new_body.splitlines()) - set(old.splitlines())
                if any(protected(l) for l in added) or protected(desc):
                    log(f"REFUSED (protected): {desc}"); continue
                if DRY:
                    log(f"would fix: {desc}"); applied += 1; continue

                open(path, "w").write(new_body)
                after, _ = verify()
                if after < before:
                    open(path, "w").write(old)
                    log(f"REVERTED in place, health {before}->{after}: {desc}"); continue
                git("add", path)
                git("-c", "user.name=Pratik Pandey", "commit", "-q", "-m",
                    f"auto-fix: {desc}\n\nApplied by scripts/self_heal.py. Health {before} -> {after}.\n"
                    f"Revert with: git revert HEAD\n\n"
                    f"Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>")
                sha = git("rev-parse", "--short", "HEAD").stdout.strip()
                log(f"FIXED [{sha}] {desc}  (health {before} -> {after})")
                before = after; applied += 1

        if applied and not DRY:
            r = git("push", "-q", "origin", "main")
            log("pushed" if r.returncode == 0 else f"push failed: {r.stderr[:120]}")
        if not applied:
            log("nothing to fix")
        final, notes = verify()
        log(f"final health {final}" + (f" | remaining, needs a person: {'; '.join(notes[:5])}" if notes else " | clean"))
    finally:
        os.path.exists(LOCK) and os.remove(LOCK)
    return 0

if __name__ == "__main__":
    sys.exit(main())

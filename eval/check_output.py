#!/usr/bin/env python3
"""
Mechanical checks on a Business Idea Validator output.

Deliberately contains no judgement. Every check here is falsifiable: arithmetic,
the skill's own stated decision rules, structural completeness, evidence labelling,
banned vocabulary, and whether cited URLs resolve. Anything requiring an opinion
about whether the analysis was *good* is out of scope on purpose - a model grading
its own reasoning tells you nothing.

Usage:  python3 eval/check_output.py <file.md> [--check-urls] [--expect VERDICT]
Exit:   0 all checks passed, 1 one or more failed.
"""
import re, sys, json, argparse

BANNED = ["SWOT", "Porter", "Five Forces", "Business Model Canvas",
          "Blue Ocean", "PESTLE", "Ansoff", "BCG Matrix"]

def load(p):
    return open(p, encoding="utf-8").read()

def find_scores(t):
    """Scorecard rows: | N | Area | Score | Reason |  (score may be **bold**)"""
    rows = re.findall(r"^\|\s*(\d{1,2})\s*\|\s*([^|]+?)\s*\|\s*\**(\d{1,2})\**\s*\|",
                      t, re.M)
    return [(int(n), a.strip(), int(s)) for n, a, s in rows if 1 <= int(s) <= 10]

def stated_average(t):
    m = re.search(r"\|\s*\**AVERAGE\**\s*\|\s*\**([\d.]+)\**", t, re.I)
    return float(m.group(1)) if m else None

def verdict(t):
    m = re.search(r"\|\s*\**DECISION\**\s*\|\s*\**(GO|CONDITIONAL GO|PIVOT|NO-GO)\**",
                  t, re.I)
    return m.group(1).upper() if m else None

def confidence(t):
    m = re.search(r"CONFIDENCE[:\s|*]+\**(High|Medium|Low)\**", t, re.I)
    return m.group(1).capitalize() if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--check-urls", action="store_true")
    ap.add_argument("--expect", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t = load(a.file)
    results = []
    def check(name, ok, detail=""):
        results.append({"check": name, "ok": bool(ok), "detail": detail})

    # 1. Structure
    for sec in ["2.1", "2.2", "2.3", "2.4", "2.5"]:
        check(f"section {sec} present", sec in t)

    # 2. Scorecard shape
    scores = find_scores(t)
    check("scorecard has 10 rows", len(scores) == 10, f"found {len(scores)}")

    # 3. Arithmetic
    stated, computed = stated_average(t), None
    if len(scores) == 10:
        computed = round(sum(s for _, _, s in scores) / 10, 2)
    if stated is not None and computed is not None:
        check("stated average matches the scores", abs(stated - computed) < 0.051,
              f"stated {stated}, computed {computed}")
    else:
        check("average row present", False, "no AVERAGE row parsed")

    # 4. The skill's own decision rules
    v, conf = verdict(t), confidence(t)
    check("decision card present", v is not None, str(v))
    if v and computed is not None:
        low = [(n, ar, s) for n, ar, s in scores if s <= 3]
        if low:
            check("deal-breaker blocks GO", v != "GO",
                  f"rows <=3: {[f'{ar}={s}' for _, ar, s in low]} -> {v}")
        if computed >= 7.5:
            check("average >=7.5 permits GO", v in ("GO", "CONDITIONAL GO", "PIVOT"), f"{computed} -> {v}")
        elif computed >= 5.5:
            check("average 5.5-7.4 is not GO", v != "GO", f"{computed} -> {v}")
        else:
            check("average <5.5 is NO-GO or PIVOT", v in ("NO-GO", "PIVOT"), f"{computed} -> {v}")
    if conf:
        check("Low confidence blocks GO", not (conf == "Low" and v == "GO"), f"{conf}/{v}")

    # 5. Evidence labelling
    labels = {k: len(re.findall(re.escape(f"[{k}]"), t)) for k in
              ("Verified", "Estimate", "Assumption")}
    total = sum(labels.values())
    words = len(t.split())
    per_1k = round(total / max(words, 1) * 1000, 1)
    check("numbers are labelled", total > 0, json.dumps(labels))
    check("labelling density >=4 per 1k words", per_1k >= 4.0,
          f"{per_1k} per 1k words ({total} labels / {words} words)")

    # 6. Banned framework vocabulary
    hits = [b for b in BANNED
            if re.search(r"\b" + re.escape(b) + r"\b", t, re.I)]
    check("no framework name-dropping", not hits, ", ".join(hits))

    # 7. Unknowns are surfaced rather than invented
    check("says Unknown where it does not know", "Unknown" in t)

    # 8. Expected verdict, when the eval case declares one
    if a.expect:
        allowed = [x.strip().upper() for x in a.expect.split("|")]
        check(f"verdict in {allowed}", v in allowed, str(v))

    # 9. Citations resolve
    if a.check_urls:
        import urllib.request
        urls = sorted(set(re.findall(r"https?://[^\s)\]]+", t)))
        dead = []
        for u in urls:
            u = u.rstrip(".,);")
            try:
                rq = urllib.request.Request(u, method="HEAD",
                     headers={"User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(rq, timeout=12)
            except Exception as e:
                code = getattr(e, "code", None)
                if code in (403, 405, 429):   # bot-blocked, not dead
                    continue
                dead.append(f"{u} ({code or type(e).__name__})")
        check("cited URLs resolve", not dead, "; ".join(dead[:5]))

    failed = [r for r in results if not r["ok"]]
    if a.json:
        print(json.dumps({"file": a.file, "passed": len(results) - len(failed),
                          "failed": len(failed), "results": results}, indent=1))
    else:
        for r in results:
            print(("  PASS  " if r["ok"] else "  FAIL  ") + r["check"] +
                  (f"  -- {r['detail']}" if r["detail"] else ""))
        print(f"\n{len(results)-len(failed)}/{len(results)} passed  [{a.file}]")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())

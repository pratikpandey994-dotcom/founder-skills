# Founder Skills

Two Claude Skills that work as a pair: one finds business ideas, the other decides whether
they are worth building.

They are deliberately separate. A system that generates an idea and then grades it will always
like what it made.

| Skill | What it does |
|---|---|
| **[Solo Founder Idea Engine](solo-founder-idea-engine/)** | Produces ideas for one person building alone — D2C, B2B, SaaS, apps, platforms, services, hardware. Every idea traced to a real, dated change in the world, with the strongest argument against it and a kill signal you can check this week. |
| **[Business Idea Validator](business-idea-validator/)** | Takes one idea and returns a decision — GO / CONDITIONAL GO / PIVOT / NO-GO — with the evidence behind it, then the roadmap from today to a working business. Built for researchers and first-time founders. |

## Why these exist

Most startup-idea tools are built for someone shipping a SaaS product. They lead with named
frameworks and they skip the things that actually decide a technical founder's outcome:
who owns the IP, how far the lab result is from production, which approval is needed and how
long it takes, and whether licensing the technology beats building a company around it.

These two cover that ground, in plain language, with no framework vocabulary.

## How they fit together

```
Solo Founder Idea Engine          Business Idea Validator
  ├─ 12 lenses on what changed      ├─ Stage 1  intake, 12 questions
  ├─ 5 ideas per run                ├─ Stage 2  diagnosis, scorecard, decision
  ├─ kill signal for each           └─ Stage 3  roadmap with stop/go gates
  └─ ledger, so it never repeats
                    │                         ▲
                    └─── paste one idea ──────┘
```

Every idea from the engine ends with a paste-ready line for the validator. Run the engine
often; run the validator on the one idea you cannot stop thinking about.

## Install

**Claude apps (claude.ai, desktop, mobile)** — the one to use if you work in chat.
```bash
git clone https://github.com/pratikpandey994-dotcom/founder-skills
cd founder-skills
zip -r business-idea-validator.zip business-idea-validator
zip -r solo-founder-idea-engine.zip solo-founder-idea-engine
```
Then Settings → Capabilities → Skills → Add skill, and upload each zip. Available on Free
through Enterprise; code execution must be enabled.

**Claude Code**
```bash
git clone https://github.com/pratikpandey994-dotcom/founder-skills
cp -R founder-skills/business-idea-validator ~/.claude/skills/
cp -R founder-skills/solo-founder-idea-engine ~/.claude/skills/
```

**A team or organisation** — on Team and Enterprise plans an admin can provision both skills
organisation-wide, so everyone runs the same version.

Turn on web search. Both skills depend on real, current facts; without search their numbers
get much weaker.

## Evidence discipline

Both skills label every number `[Verified]`, `[Estimate]` or `[Assumption]`, size markets
bottom-up from countable buyers rather than from "the global X market is worth $Y billion",
and write **Unknown** where they do not know, with how to find out. Neither invents a company,
a statistic, a law or a source.

## The ledger

`solo-founder-idea-engine/references/ledger.md` records every idea proposed, which lenses were
used, and what became of each one. Read before generating, appended after. It is what makes
the engine worth running fifty times instead of once.

Record the dead ideas and why they died. Over time that becomes the most useful file here.

## Licence

MIT — see [LICENSE](LICENSE).

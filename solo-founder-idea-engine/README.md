# Solo Founder Idea Engine

A Claude Skill that produces business ideas for one person building alone — D2C, B2B, SaaS,
apps, platforms, services, hardware — each one traced to a real, dated change in the world.

It is the front half of a pair. This skill finds ideas. The **Business Idea Validator** skill
judges them. Keep them separate on purpose: a generator that also grades its own output will
always like what it made.

## The method

Most AI idea generation fails the same way — it produces things that sound like businesses and
describe nothing, because it is recombining words rather than observing the world.

This skill can only start from a **change**: a price that collapsed, a rule with a compliance
date, a capability that stopped needing a specialist, a segment an incumbent walked away from,
a population curve crossing a threshold. Twelve such lenses, in `references/lenses.md`. If it
cannot name the change with a source and a date, it is required to drop the idea rather than
dress it up.

Every idea comes with the strongest argument against it, and a **kill signal** — one fact the
founder can check this week, for nearly nothing, that would end it. The point is to fail ideas
in an hour instead of a quarter.

## Each run gives you five ideas

With coverage rules, so the output does not collapse into software-for-people-like-me:

- at least two outside software
- at least one in the 1–3 or 3–7 year horizon, anchored to something already scheduled
- at least one deliberately unglamorous
- all five from different lenses

Every idea carries a four-gate solo-founder test — build, sell, cash, survive — and where it
fails a gate, what that failure costs.

## The ledger is the important part

`references/ledger.md` records every idea proposed, the lenses used, and what happened to each.
Read before generating, appended after. It is what makes the skill worth running repeatedly
rather than once: without it, run fifty produces run one again.

Record the dead ideas and why they died. That file becomes more valuable than any single run.

## Install

**Claude apps** — zip this folder with the folder itself as the zip root, then
Settings → Capabilities → Skills → Add skill.
```
zip -r solo-founder-idea-engine.zip solo-founder-idea-engine
```
**Claude Code** — copy the folder into `~/.claude/skills/`.

**Team or Enterprise** — an admin can provision it organisation-wide.

Turn on web search. Without it the skill cannot do the one thing it is built to do, which is
find changes that actually happened.

## Running it continuously

Ask for ideas whenever you want them, or set it on a schedule — in Claude Code,
`/loop 1d run the Solo Founder Idea Engine`. Weekly or daily is sensible. Faster than daily and
the world has not changed enough to have anything new to say, and you will get repeats.

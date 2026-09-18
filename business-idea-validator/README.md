# Business Idea Validator

A Claude Skill that takes a business idea from a researcher or first-time founder and returns
a straight decision with evidence behind it, then the path to build it.

Built for people who have never started a business: scientists, engineers, researchers.
It covers what generic startup tools skip — university IP ownership, lab-to-production
scale-up, regulatory approval pathways, and licensing the technology instead of building
a company.

## What it does

Three stages, one idea per conversation.

1. **Intake** — asks up to 12 questions only the founder can answer. Market facts are the AI's job.
2. **Diagnosis** — ten areas analysed, a pre-mortem, a scorecard, and a verdict:
   GO / CONDITIONAL GO / PIVOT / NO-GO, with conditions and pass/fail tests.
3. **Roadmap** — only on request, and only if the verdict allows it. Dated phases, each with
   cost, owner, duration and a stop/go gate.

Every number is labelled `[Verified]`, `[Estimate]` or `[Assumption]`. Markets are sized
bottom-up from countable buyers, never from "the global X market is worth $Y billion".

## Install

**Claude apps (claude.ai, desktop, mobile)** — this is the one to use if you work in chat.
1. Zip this folder so the folder itself is the root of the zip:
   `zip -r business-idea-validator.zip business-idea-validator`
2. In Claude: Settings → Capabilities → Skills → Add skill → upload the zip.
3. Turn the skill on. Code execution must be enabled.

**Claude Code**
Copy this folder into `~/.claude/skills/` for yourself, or `.claude/skills/` in a repo
to share it with everyone working in that repo.

**A whole team or organisation (Team and Enterprise plans)**
An owner or admin can provision the skill organisation-wide from the admin settings, so it
appears for every member automatically and everyone runs the same version.

## How to use it

Start a new conversation, turn on web search, and describe your idea in a few sentences.
The analysis depends on real, current facts, so without web search the numbers are weaker.

Answer the intake questions — "don't know" is a useful answer. You get the diagnosis and the
decision. Correct anything it got wrong, then reply `roadmap` for the full plan.

One idea per conversation.

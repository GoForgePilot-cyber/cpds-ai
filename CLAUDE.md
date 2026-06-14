# CPDS-AI — Claude Code Operating Manual

> **READ THIS FILE FIRST. EVERY SESSION. NO EXCEPTIONS.**
> After reading, run the Session Start Checklist below before touching any code.

---

## Project Identity

**What:** Cross Platform Demand Signals — a paid weekly newsletter delivering niche demand intelligence to builders and operators. Curates EMIS output + supplementary sources into free/paid split issues via Beehiiv.

**Paths:**
- Project root (WSL): `/mnt/d/Projects/cpds-ai`
- EMIS drop zone (read-only): `/mnt/d/Projects/emis-exports/digest/`
- Repo: `GoForgePilot-cyber/cpds-ai` (private, branch: `main`)
- Python venv: `~/venvs/ai-research/bin/python`

**Hard isolation rule:** NEVER read from, write to, or modify anything under `/mnt/d/Projects/claude-hermes-ai-research-scaffold`. Data flows one way: EMIS → drop zone → CPDS-AI. Violation = corrupted research pipeline.

---

## Session Start Checklist

Run these commands before writing a single line of code:

**WSL**
```bash
cd /mnt/d/Projects/cpds-ai
git status
git log --oneline -5
cat CLAUDE.md | head -80
cat config/vertical.yml
ls logs/sessions/ | tail -3
ls /mnt/d/Projects/emis-exports/digest/ 2>/dev/null || echo "No EMIS exports yet"
```

Then read the latest session log in `logs/sessions/`. If there's no session log yet, you're starting fresh — proceed to the Task Queue below.

---

## Agent Roles

| Agent | Role |
|---|---|
| Claude (claude.ai) | Architect, decision maker, strategic advisor |
| Claude Code | All file writes, all code, all edits — never diffs or partials, always complete files |

**Formatting rules (non-negotiable):**
- Label every command with window context (WSL, PowerShell, Browser) as plain text above the code block — never inside it
- Complete files on every write — never patches, never diffs
- Never ask the user to paste code manually — write it to disk directly

---

## Phase Table

| Phase | What | Status | Trigger to advance |
|---|---|---|---|
| 0 | Scaffold + platform setup | **Done — 2026-06-14** | — |
| 1 | 7-day build sprint | **In progress — 2026-06-14 to 2026-06-20** | All scripts run end-to-end, test draft in Beehiiv |
| 2 | Vertical selection + vertical config | Not started | EMIS digest available ~2026-06-28 |
| 3 | Commercial sources + first real issue | Not started | vertical.yml populated |
| 4 | Launch — first published issue + community post | Not started | First real draft reviewed |
| 5 | Growth — newsletter swaps + sponsor outreach | Not started | 200 free subscribers |
| 6 | Paid conversion flip | Not started | 50 paid subscribers |

**Current phase: 1** — 7-day build sprint. Task queue is below.

---

## Task Queue — Phase 1 (work through in order)

Tasks are labelled with owner. Claude Code executes all code tasks autonomously.

### Day 1 tasks (completed when scaffold exists and Beehiiv keys are in env)

- [ ] **[Claude Code]** Create full directory structure: `scripts/`, `sources/`, `config/`, `templates/`, `logs/sessions/`, `drafts/`, `analysis/`, `scheduler/`
- [ ] **[Claude Code]** Write `requirements.txt`
- [ ] **[Claude Code]** Write `config/vertical.yml` (placeholder — populated June 28)
- [ ] **[Claude Code]** Write `config/forums.yml`
- [ ] **[Claude Code]** Write `config/sources.yml`
- [ ] **[Claude Code]** Write `.env.example`
- [ ] **[User]** Sign up for Beehiiv Scale ($43/mo), get API key + publication ID, add to `.env`
- [ ] **[User]** Enable paid subscriptions in Beehiiv: $19/month, $190/year (annual as default)
- [ ] **[User]** Get GitHub personal access token, add to `.env`

### Day 2 tasks (Tier 1 free source ingestion)

- [ ] **[Claude Code]** Write `sources/hn_source.py`
- [ ] **[Claude Code]** Write `sources/github_source.py`
- [ ] **[Claude Code]** Write `sources/forum_source.py`
- [ ] **[Claude Code]** Write `sources/trends_source.py`
- [ ] **[Claude Code]** Write `sources/devto_source.py`
- [ ] **[Claude Code]** Write `sources/source_runner.py`
- [ ] **[User]** Run `source_runner.py`, verify output in `sources/weekly_signals.json`

### Day 3 tasks (commercial signals + EMIS bridge)

- [ ] **[Claude Code]** Write `sources/producthunt_source.py`
- [ ] **[Claude Code]** Write `sources/emis_bridge.py`
- [ ] **[Claude Code]** Update `source_runner.py` to include new sources
- [ ] **[User]** Request Product Hunt developer token at developers.producthunt.com

### Day 4 tasks (curate.py — the core draft generator)

- [ ] **[Claude Code]** Write `templates/free_section.md.j2`
- [ ] **[Claude Code]** Write `templates/paid_section.md.j2`
- [ ] **[Claude Code]** Write `scripts/beehiiv_publisher.py`
- [ ] **[Claude Code]** Write `scripts/curate.py`
- [ ] **[User]** Add Anthropic API key to `.env`
- [ ] **[User]** Run `curate.py` against placeholder data, review draft in Beehiiv
- [ ] **[User]** Flag prompt quality issues for Claude Code to fix

### Day 5 tasks (social automation + prompt tuning)

- [ ] **[Claude Code]** Revise `scripts/curate.py` prompts based on user review
- [ ] **[Claude Code]** Write `scripts/social_post.py`
- [ ] **[Claude Code]** Write `scripts/analytics_digest.py`

### Day 6 tasks (scheduler + Beehiiv config)

- [ ] **[Claude Code]** Write `scheduler/source_runner_task.xml`
- [ ] **[Claude Code]** Write `scheduler/curate_task.xml`
- [ ] **[Claude Code]** Write `scheduler/analytics_task.xml`
- [ ] **[Claude Code]** Write `scheduler/register_tasks.bat`
- [ ] **[Claude Code]** Write welcome email copy: `templates/welcome_free.md` and `templates/welcome_paid.md`
- [ ] **[User]** Configure Beehiiv welcome automations using welcome email templates
- [ ] **[User]** Configure paywall appearance in Beehiiv

### Day 7 tasks (end-to-end test + milestone review)

- [ ] **[User]** Run full pipeline: `source_runner.py` → `curate.py` → review Beehiiv draft
- [ ] **[User]** Edit test draft (20–30 min), verify free/paid split looks correct
- [ ] **[Claude Code]** Fix any issues from test run
- [ ] **[Claude Code]** Run Phase 1 milestone analysis → write `analysis/milestone_phase1.md`
- [ ] **[Claude Code]** Update this CLAUDE.md phase table (Phase 1 → Done)
- [ ] **[Claude Code]** Write `logs/sessions/session_20260620.md`
- [ ] **[Claude Code]** Commit everything: `git add -A && git commit -m "feat: phase 1 complete — full pipeline operational" && git push origin main`

---

## Recursive Self-Improvement Protocol

This is not optional. Claude Code runs this at every milestone and whenever it notices drift.

### Trigger conditions
Run a self-improvement cycle when any of these occur:
1. A phase completes (milestone review)
2. A source starts returning empty or low-quality data consistently (>2 runs)
3. curate.py draft quality is below threshold (flagged by user or detected via low word count / high template fill ratio)
4. A new source type becomes available that wasn't in the original plan
5. User flags something isn't working
6. 4 weeks have passed since last improvement cycle

### What a self-improvement cycle does

Claude Code runs `scripts/self_improve.py` which:

1. **Reads all current source outputs** — assesses signal quality, volume, duplication rate
2. **Reads all session logs** — extracts patterns: what took too long, what errors recurred, what the user flagged
3. **Reads all milestone analysis files** — tracks drift against original plan
4. **Calls Claude API** with a structured analysis prompt covering:
   - Source health: which sources are delivering, which are noisy or dead
   - Prompt quality: is curate.py producing output worth $19/month or generic summaries
   - Distribution drift: are community posts working, are swap partnerships progressing
   - Viability signals: subscriber growth rate vs. target, paid conversion rate vs. benchmark
   - New opportunities: sources, monetization angles, or content formats not in the original plan
   - Dead ideas: what the plan assumed that the data now contradicts
5. **Writes structured report** to `analysis/improvement_YYYY-MM-DD.md`
6. **Proposes specific code changes** — modifies its own prompt templates, source weights, or config if analysis supports it
7. **Updates CLAUDE.md** task queue with any new tasks generated by the analysis

### Self-improvement is not permission to rewrite everything

Rules for what self-improvement can and cannot change autonomously:
- **Can change:** prompt templates, source filters, keyword lists in config, output formatting, scheduling intervals
- **Requires user approval:** adding paid API sources (cost), changing the free/paid content split, changing pricing or platform, adding new distribution channels
- **Never changes without explicit instruction:** EMIS bridge behavior, isolation rules, the business model core

---

## Milestone Analysis Protocol

At the end of each phase, Claude Code runs a deep-dive viability analysis. This is more thorough than the self-improvement cycle — it's a business review, not a code review.

### What gets analyzed at each milestone

**Signal drift:** Are the sources still picking up the signals they were designed to? Has the community moved somewhere new? Are new platforms emerging that weren't in scope?

**Viability check:** Run the actual numbers against the benchmarks from the original research:
- Free subscribers vs. target trajectory
- Paid conversion rate vs. 1–3% benchmark
- Open rate vs. 40%+ target
- Churn vs. 5% monthly expected
- If any metric is >20% below target for 4+ weeks: flag as viability risk, propose corrective action

**Idea audit:**
- Dead ideas: what was planned that data now shows won't work
- Better ideas: what's emerged from signals or subscriber behavior that wasn't in the original plan
- New ideas: what the signal stack is surfacing that could be a content angle, monetization path, or distribution channel not previously considered

**Competitive drift:** Have new newsletters launched in the vertical? Has an incumbent strengthened? Has the niche shifted enough to reconsider the vertical selection?

**Output:** `analysis/milestone_phaseN.md` — structured, honest, no filler. This file is read by Claude.ai (architect) to make strategic decisions.

---

## Architecture: Free vs Paid Content Split

**Rule:** Free content builds the case. Paid content delivers the verdict.

### Free section (sent to all subscribers)
1. Signal Snapshot — 3 demand signals this week, 1–2 sentences of context each
2. What's Moving — 1 stat or trend showing volume/velocity
3. Community Pulse — 2–3 direct quotes from forums/Discord showing practitioner sentiment
4. [PAYWALL BREAK — Beehiiv section visibility gate]
5. Paid preview — one sentence describing what paid subscribers got (no spoilers)
6. Free resource — one useful link or tool (goodwill, not a teaser of nothing)

### Paid section (paid subscribers only, via Beehiiv section gate)
1. Full Signal Analysis — why these signals matter together, not just individually
2. Commercial Layer — what Fiverr/Upwork gig data + LinkedIn hiring shows about buyer spending
3. The Specific Opportunity — what to build, pitch, or position this week
4. Launches Worth Watching — Product Hunt / GitHub launches with editorial take
5. Actionable Template — one reusable prompt, pricing model, or outreach angle
6. Next Week Watch — what EMIS is tracking for the following issue

### Beehiiv implementation
- Single post, single send, full list
- Section visibility gate at the paywall break (not a full post paywall)
- Free readers see content above gate, hit paywall prompt, see one-line paid preview
- Paid readers see everything continuously

---

## Source Architecture

### Tier 1 — Free APIs, run every Saturday 9pm

| Source | File | API | Signal type |
|---|---|---|---|
| Hacker News | `sources/hn_source.py` | Firebase + Algolia (free) | Launches, hiring, pain |
| GitHub | `sources/github_source.py` | REST API (free, auth) | Repo velocity, adoption |
| n8n Forum | `sources/forum_source.py` | Discourse RSS/JSON (free) | Practitioner pain |
| Indie Hackers | `sources/forum_source.py` | Algolia endpoint (free) | Revenue validation |
| Google Trends | `sources/trends_source.py` | pytrends (free) | Demand velocity |
| DEV.to | `sources/devto_source.py` | Forem API (free) | Solution patterns |
| EMIS bridge | `sources/emis_bridge.py` | Local file read | Synthesized signals |

### Tier 2 — Add after vertical confirmed

| Source | File | Cost | Signal type |
|---|---|---|---|
| Product Hunt | `sources/producthunt_source.py` | Free API token | Launch traction |
| Fiverr | `sources/fiverr_source.py` | Apify ~$0.003/gig | Buyer demand patterns |
| Upwork | `sources/upwork_source.py` | Apify ~$0.003/job | Budget + intent |
| Stack Overflow | `sources/stackoverflow_source.py` | Free API | Technical pain |

### Tier 3 — Post-launch additions (200+ subscribers)

- Discord bot (n8n official server)
- Exploding Topics Pro ($49/mo)
- Crunchbase funding alerts (free tier)

---

## Weekly Automated Schedule

| Time | Task | Script |
|---|---|---|
| Saturday 9pm | Pull all signals | `source_runner.py` |
| Sunday 6am | Generate draft → push to Beehiiv | `curate.py` |
| Sunday ~7am | User reviews draft (20–30 min) | Manual |
| Sunday morning | User sends newsletter | Manual (Beehiiv) |
| Sunday post-send | Generate social posts | `social_post.py` |
| Sunday post-send | User posts to LinkedIn/X | Manual (review social drafts) |
| Monday 8am | Pull analytics digest | `analytics_digest.py` |

**Total weekly time budget: 45–60 minutes human time.**

---

## Operating Rules

1. Direct, businesslike, concise — no filler in code or comments
2. Complete files on every write — never diffs or partials
3. Label every command with window context (WSL, PowerShell) as plain text above the block
4. Automate everything repeatable
5. Touch only what the request requires
6. Never cross into EMIS files
7. Session audit required at end of every meaningful session
8. Self-improvement cycle required at every phase milestone
9. When in doubt about a business decision, write `analysis/question_YYYY-MM-DD.md` and flag for Claude.ai review

---

## Session End Protocol

Required at the end of every meaningful session:

**Claude Code:**
```bash
# WSL
cd /mnt/d/Projects/cpds-ai
```
1. Update phase table in this CLAUDE.md (mark completed tasks with [x])
2. Write `logs/sessions/session_YYYYMMDD.md` with: what was built, what broke, what's next, any flags for Claude.ai
3. Commit:
```bash
# WSL
git add -A && git commit -m "docs: session audit YYYY-MM-DD — [one line summary]" && git push origin main
```

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
cat config/vertical.yml
ls logs/sessions/ | tail -3
ls /mnt/d/Projects/emis-exports/digest/ 2>/dev/null || echo "No EMIS exports yet"
```

Then read the latest session log in `logs/sessions/` before doing anything else.

---

## Agent Roles

| Agent | Role |
|---|---|
| Claude (claude.ai) | Architect, decision maker, strategic advisor |
| Claude Code | All file writes, all code, all edits — never diffs or partials, always complete files |

**Formatting rules (non-negotiable):**
- Label every command with window context (WSL, PowerShell) as plain text above the code block — never inside it
- Complete files on every write — never patches, never diffs
- Never ask the user to paste code manually — write it to disk directly
- Version headers in every script file: version number, last updated date, changelog

---

## Phase Table

| Phase | What | Status | Trigger to advance |
|---|---|---|---|
| 0 | Scaffold + platform setup | **Done — 2026-06-14** | — |
| 1 | 7-day build sprint | **Done — 2026-06-15** | Pipeline runs end-to-end ✓ |
| 2 | Vertical selection + vertical config | **Waiting — ~2026-06-28** | EMIS digest available |
| 3 | Commercial sources + first real issue | Not started | vertical.yml populated |
| 4 | Launch — first published issue + community post | Not started | First real draft reviewed and sent |
| 5 | Growth — newsletter swaps + sponsor outreach | Not started | 200 free subscribers |
| 6 | Paid conversion flip | Not started | 50 paid subscribers |

**Current phase: 2 (waiting)** — Pipeline is operational. Waiting for EMIS vertical selection ~June 28.

---

## Current State — What Works

All Phase 1 code is complete and tested. The following run correctly:

- `sources/source_runner.py` — pulls HN, GitHub, forum (IH via RSS), Trends, DEV.to, EMIS bridge
- `scripts/curate.py` v1.4.0 — two Claude API calls, generates free + paid drafts
- `templates/free_section.md.j2` v1.3.0 — CPDS Intelligence Network branding, no source attribution
- `templates/paid_section.md.j2` — full paid post template
- `scripts/beehiiv_publisher.py` — two-post model (free post all subscribers, paid post paid only)
- `scripts/social_post.py` — generates LinkedIn/X/community post drafts
- `scripts/analytics_digest.py` — weekly Beehiiv stats pull
- `scripts/self_improve.py` — recursive self-improvement engine
- `scripts/milestone_analysis.py` — phase milestone deep-dive analysis
- `scheduler/` — XML task files and register_tasks.bat (not yet registered)

**Known issues / workarounds:**
- Indie Hackers Algolia endpoint DNS-blocked on WSL NAT — using RSS fallback (works)
- Google Trends 429 on consecutive runs — works fine on weekly cadence
- Beehiiv post creation API is Enterprise-only — posting via browser clipboard injection (5 min manual per post)

---

## Task Queue — Phase 2 (next session ~June 28)

### Claude Code does on next session start

1. Read latest EMIS digest from `/mnt/d/Projects/emis-exports/digest/`
2. Run `scripts/self_improve.py --trigger phase_transition` — get improvement report before starting
3. Read `analysis/` for any pending flags from Claude.ai

### User actions still pending

- [ ] Register Task Scheduler tasks — run as Administrator in PowerShell:
  ```
  cd D:\Projects\cpds-ai\scheduler
  .\register_tasks.bat
  ```
- [ ] Beehiiv plan decision before June 28 — Max trial expires. Scale plan ($43/mo) needed for paid subscription tiers. Without it, paid post audience segmentation won't work.
- [ ] Request Product Hunt API token — developers.producthunt.com (free, 1-2 day approval)
- [ ] Beehiiv: configure welcome email automations using `templates/welcome_free.md` and `templates/welcome_paid.md`
- [ ] Beehiiv: set paid subscription pricing ($19/month, $190/year, annual as default)

### Claude Code actions on June 28

When user confirms EMIS digest is available and vertical is selected:

1. Read EMIS digest, confirm vertical selection with user
2. Populate `config/vertical.yml` — set status: active, fill all keyword/topic fields
3. Enable Tier 2 sources in `config/sources.yml` (Product Hunt if token available)
4. Update `curate.py` prompts for the specific vertical (replace generic language with vertical-specific framing)
5. Enable Fiverr/Upwork sources if Apify token available
6. Run `source_runner.py` with live vertical config — verify signal quality
7. Run `curate.py` — review first real draft
8. Write `logs/sessions/session_20260628.md`
9. Commit and push

---

## Content Architecture

### Title format
`Jun 15 · [6-8 word headline]` — no issue numbers, date handles sequencing

### Source attribution
Always: "CPDS Intelligence Network" — never name HN, GitHub, Reddit, EMIS, or any specific platform

### Free post (all subscribers)
1. Signal snapshot — 3 signals, 1-2 sentences each, no source links
2. What's moving — 1 stat with number
3. Community pulse — 2-3 quotes, attributed to practitioner roles not platforms
4. Paid teaser — one line, no spoilers
5. Free resource — one useful URL

### Paid post (paid subscribers only)
1. Full signal analysis — synthesis, not description
2. Commercial layer — Fiverr/Upwork/hiring signals
3. Specific opportunity — what to build/pitch/position
4. Launches worth watching — with editorial take
5. Actionable template — reusable prompt/framework/script
6. Next week watch — 3 specific topics EMIS is tracking

### Posting workflow (Beehiiv)
1. Pipeline runs Saturday 9pm → Sunday 6am draft saved to `drafts/YYYY-MM-DD_free.md` and `_paid.md`
2. User opens Beehiiv → New post → paste free draft body → set title → Next through to audience (all subscribers) → save draft
3. Repeat for paid post → audience: paid subscribers only
4. Review both drafts → send free first → send paid
5. Total manual time: ~10 minutes

---

## Weekly Schedule (once Task Scheduler registered)

| Time | Task | Script |
|---|---|---|
| Saturday 9pm | Pull all signals | `source_runner.py` |
| Sunday 6am | Generate drafts | `curate.py` |
| Sunday ~7am | User pastes drafts to Beehiiv, reviews, sends | Manual (~10 min) |
| Sunday post-send | Generate social post drafts | `social_post.py` |
| Sunday post-send | User posts to LinkedIn/X (edits social drafts first) | Manual (~10 min) |
| Monday 8am | Analytics digest | `analytics_digest.py` |

---

## Self-Improvement Protocol

Run `scripts/self_improve.py` at:
- Every phase transition
- Any source returning empty >2 consecutive runs
- User flags content quality issue
- Every 4 weeks regardless

Auto-apply: prompt edits, keyword lists, source config weights
Requires approval: new paid sources, platform changes, pricing changes
Never auto-changes: EMIS isolation rules, business model core

---

## Milestone Analysis Protocol

Run `scripts/milestone_analysis.py --phase N` at end of each phase.
Output: `analysis/milestone_phaseN_YYYY-MM-DD.md`
Read by Claude.ai before next phase begins.
Covers: phase verdict, business health, drift analysis, idea audit, competitive assessment, kill criteria.

---

## Kill Criteria (set now, enforced later)

These are not targets — they are triggers to stop or pivot:

| Milestone | Kill condition | Action |
|---|---|---|
| Week 8 post-launch | < 150 free subscribers | Pivot vertical or kill |
| Week 4 after paid open | 0 paid conversions | Rewrite value prop |
| Month 6 | < 30 paid subscribers | Shut down or restructure |
| Any time | Open rate < 25% for 3 consecutive issues | Review content quality |

---

## Operating Rules

1. Direct, businesslike, concise — no filler
2. Complete files on every write — never diffs or partials
3. Label every command with window context (WSL, PowerShell) as plain text above the block
4. Version headers in every script: version, date, changelog
5. Automate everything repeatable
6. Touch only what the request requires
7. Never cross into EMIS files
8. Session audit required at end of every meaningful session
9. Self-improvement cycle required at every phase milestone

---

## LLM Provider Switching

All LLM calls in CPDS-AI must use the provider abstraction established in EMIS.
Non-negotiable — applies to all new scripts and future projects.

| Provider | Model | Cost | Use |
|---|---|---|---|
| `cerebras` | gpt-oss-120b | Free (1M tok/day) | Dev/test default |
| `groq` | llama-3.3-70b-versatile | Free tier | Dev/test |
| `ollama` | qwen2.5:7b (JSON) / gemma3:12b (research) | Free (local GPU) | Offline |
| `anthropic` | claude-sonnet-4-20250514 | Paid | Production quality |

**Pattern for any new LLM call:**
```python
from shared.llm_client import LLMClient  # shared/ from EMIS — or port to cpds-ai/shared/
provider = os.getenv("LLM_PROVIDER", "cerebras")  # default to free
client = LLMClient(provider=provider)
```

**CLI flag on any script that calls LLM:**
```bash
python scripts/curate.py --provider cerebras   # free
python scripts/curate.py --provider anthropic  # production quality
```

**Env var (applies to all scripts without flag):**
```
LLM_PROVIDER=cerebras  # in .env
```

**Cerebras model note:** Model catalog changes frequently.
Always verify at https://inference-docs.cerebras.ai/models/overview before use.
Current production model: `gpt-oss-120b` (as of 2026-06-15)

**Quality expectation:**
- Anthropic: 83-91/100 quality score on EMIS synthesis
- Cerebras: 66/100 on EMIS synthesis (no web search, Reddit-only input)
- For CPDS-AI curation (structured formatting, not open-ended research): Cerebras adequate
- For production issues sent to subscribers: evaluate quality before committing to Cerebras only

---

## Session End Protocol

1. Update phase table in this CLAUDE.md
2. Mark completed tasks in task queue
3. Write `logs/sessions/session_YYYYMMDD.md`
4. Commit:

**WSL**
```bash
git add -A && git commit -m "docs: session audit YYYY-MM-DD — [one line summary]" && git push origin main
```

# CPDS-AI — Claude Operating Brief

## Project Identity

**Project name**: Cross Platform Demand Signals (CPDS-AI)
**Directory**: `D:\Projects\cpds-ai`
**WSL path**: `/mnt/d/Projects/cpds-ai`
**Brand**: CPDS-AI (separate from CoForgePilot AI)
**Purpose**: Paid newsletter business delivering niche market intelligence

## Isolation Rules

This project is completely separate from EMIS.

- Do NOT read from `D:\Projects\claude-hermes-ai-research-scaffold\` directly
- Do NOT modify any EMIS files from this project
- Do NOT share config, credentials, or code with EMIS
- Data flows ONE WAY: EMIS → `D:\Projects\emis-exports\` → CPDS-AI
- If you need EMIS to change something, flag it — do not cross-edit

## Read First

Before any development work:

1. This file (`CLAUDE.md`)
2. `logs/sessions/` — latest session audit
3. `config/vertical.yml` — current target vertical and status
4. Check `D:\Projects\emis-exports\digest\` for latest available content

## Operating Style

Same discipline as EMIS:
- Direct, businesslike, concise
- No filler, no affirmations
- Complete files on every edit
- Label every command with window context (WSL, PowerShell)
- Automate everything repeatable — no manual workflows

## Architecture

```
D:\Projects\emis-exports\digest\     ← EMIS drop zone (read-only for CPDS)
        ↓
scripts/curate.py                    ← pulls latest digest, strips noise, formats draft
        ↓
content/drafts/YYYY-MM-DD.md         ← human review (20-30 min)
        ↓
scripts/publish.py                   ← pushes to Substack via API
        ↓
content/published/YYYY-MM-DD.md      ← archive
```

## Target Audience

TBD — waiting for EMIS 2-week signal run to identify vertical.
Candidates: n8n automation services, niche microsaas, AI billing infrastructure.

## Monetization

- Phase 1: Free newsletter on Substack — build to 50 subscribers
- Phase 2: Flip to paid at $19/month once 50 active subscribers confirmed
- Milestone to flip: 50 subscribers opening consistently

## Weekly Time Budget

2-4 hours total:
- 20-30 min: review curated draft from `scripts/curate.py`
- 30 min: light editing and personal context
- 30 min: publish and post in target community
- Remainder: respond to replies, track growth

## Agent Roles

| Agent | Role |
|---|---|
| Claude (claude.ai) | Architect, decision maker |
| Claude Code | Implementation — all file writes |

## Phase Table

| Phase | What | Status |
|---|---|---|
| 0 | Scaffold + isolation setup | Done — 2026-06-14 |
| 1 | EMIS vertical selection (2-week signal run) | Waiting |
| 2 | Community validation post | Not started |
| 3 | Substack setup + first issue | Not started |
| 4 | Paid conversion at 50 subscribers | Not started |

## Key Files

| File | Purpose |
|---|---|
| `config/vertical.yml` | Target vertical, community, Substack slug |
| `config/publishing.yml` | Schedule, format rules, curation criteria |
| `scripts/curate.py` | Pulls EMIS exports, formats draft issue |
| `scripts/publish.py` | Pushes draft to Substack API (placeholder) |
| `.env` | Substack API key, email credentials |

## Git Rules

Same as EMIS — no secrets, no force push, commit message format:
- `feat:` new feature
- `fix:` bug fix
- `docs:` session audit or documentation
- `chore:` config, scaffolding

## Session Audit Protocol

End every session with:
1. Update `CLAUDE.md` Phase Table
2. Write `logs/sessions/session_YYYYMMDD.md`
3. Commit: `git add CLAUDE.md logs/sessions/ && git commit && git push`

## What NOT to Build Without Explicit Instruction

- No LLM pipeline — EMIS handles analysis, CPDS-AI curates output
- No database — flat files and Substack are sufficient for v1
- No web scraping — EMIS handles all data collection
- No shared infrastructure with EMIS
- No UI or dashboard in v1

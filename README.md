# CPDS-AI — Cross Platform Demand Signals

Autonomous market intelligence newsletter powered by EMIS signal output.

## What this is

A focused newsletter business that curates demand signals from the EMIS pipeline
and delivers them as a weekly paid digest to a specific niche audience.

## What this is NOT

- Not a copy of EMIS
- Not a replacement for EMIS
- Not connected to CoForgePilot AI internal tooling
- Does not write to or read from the EMIS project directory directly

## Data source

EMIS exports digests to `D:\Projects\emis-exports\` via:

```bash
bash /mnt/d/Projects/claude-hermes-ai-research-scaffold/scripts/export_to_cpds.sh
```

CPDS-AI reads from that drop zone only.

## Stack

- Python 3.11 (WSL2 Ubuntu)
- Substack (newsletter delivery + payments)
- Minimal dependencies — no database, no LLM calls in v1

## Project structure

```
cpds-ai/
  config/           ← vertical config, publishing settings
  scripts/          ← curation helper, publish automation
  content/
    drafts/         ← issues in progress
    published/      ← archive of sent issues
  logs/             ← run logs
  .env.example      ← credentials template
  CLAUDE.md         ← operating brief
  README.md
```

## Status

Pre-launch. Waiting for EMIS to identify target vertical via 2-week signal run.

#!/bin/bash
# CPDS-AI Bootstrap Script
# Run once to set up the full project from a clean clone
# WSL: bash scripts/bootstrap.sh

set -e

echo ""
echo "============================================================"
echo "CPDS-AI Bootstrap — setting up project from scratch"
echo "============================================================"
echo ""

PROJECT_ROOT="/mnt/d/Projects/cpds-ai"
VENV_PYTHON="$HOME/venvs/ai-research/bin/python"

# Check we're in the right place
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: $PROJECT_ROOT does not exist"
    echo "Clone the repo first: git clone ... $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"
echo "[bootstrap] Working in: $(pwd)"

# Check Python venv
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Python venv not found at $VENV_PYTHON"
    echo "Create it: python3 -m venv ~/venvs/ai-research"
    exit 1
fi

echo "[bootstrap] Python: $($VENV_PYTHON --version)"

# Create directory structure
echo "[bootstrap] Creating directory structure..."
mkdir -p scripts sources config templates logs/sessions logs/scheduler drafts analysis scheduler

# Install dependencies
echo "[bootstrap] Installing Python dependencies..."
"$VENV_PYTHON" -m pip install -r requirements.txt --quiet

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Created .env from .env.example"
    echo "    Add your API keys before running any scripts:"
    echo ""
    echo "    Required now:"
    echo "      ANTHROPIC_API_KEY   — https://console.anthropic.com/settings/keys"
    echo "      BEEHIIV_API_KEY     — Beehiiv dashboard → Settings → API"
    echo "      BEEHIIV_PUB_ID      — visible in Beehiiv dashboard URL"
    echo "      GITHUB_TOKEN        — https://github.com/settings/tokens"
    echo ""
    echo "    Required later (after vertical selection):"
    echo "      PRODUCTHUNT_API_KEY — https://www.producthunt.com/v2/oauth/applications"
    echo "      APIFY_API_TOKEN     — https://apify.com (Tier 2 commercial sources)"
    echo ""
else
    echo "[bootstrap] .env already exists — skipping"
fi

# Create seen_ids.json if it doesn't exist
if [ ! -f "sources/seen_ids.json" ]; then
    echo "{}" > sources/seen_ids.json
    echo "[bootstrap] Created sources/seen_ids.json"
fi

# Create github_stars.json if it doesn't exist
if [ ! -f "sources/github_stars.json" ]; then
    echo "{}" > sources/github_stars.json
    echo "[bootstrap] Created sources/github_stars.json"
fi

# Verify git status
echo ""
echo "[bootstrap] Git status:"
git status --short

echo ""
echo "============================================================"
echo "Bootstrap complete."
echo ""
echo "Next steps:"
echo ""
echo "  1. Fill in .env with your API keys"
echo "  2. Activate Beehiiv Scale plan ($43/mo) and enable paid subscriptions"
echo "  3. Test the pipeline:"
echo ""
echo "     WSL"
echo "     # Test sources (uses placeholder vertical)"
echo "     $VENV_PYTHON sources/source_runner.py"
echo ""
echo "     # Test draft generation (requires ANTHROPIC_API_KEY + BEEHIIV_API_KEY)"
echo "     $VENV_PYTHON scripts/curate.py"
echo ""
echo "  4. Register scheduled tasks (run as Administrator in PowerShell):"
echo ""
echo "     PowerShell"
echo "     cd D:\\Projects\\cpds-ai\\scheduler"
echo "     .\\register_tasks.bat"
echo ""
echo "  5. Read CLAUDE.md — the full operating manual"
echo "============================================================"
echo ""

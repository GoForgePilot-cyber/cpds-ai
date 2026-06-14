#!/usr/bin/env python3
"""curate.py — Pull latest EMIS digest exports and format a draft newsletter issue.

Reads from D:\\Projects\\emis-exports\\digest\\
Writes draft to content/drafts/YYYY-MM-DD.md

Usage:
    python scripts/curate.py
    python scripts/curate.py --date 20260614    # curate a specific digest date
    python scripts/curate.py --dry-run          # print draft to stdout, don't write file
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTS_DIR  = Path("/mnt/d/Projects/emis-exports/digest")
DRAFTS_DIR   = PROJECT_ROOT / "content" / "drafts"

# ── helpers ───────────────────────────────────────────────────────────────────

def find_latest_digest(date_filter: str | None = None) -> Path | None:
    """Return the most recent .md file in the exports directory."""
    if not EXPORTS_DIR.exists():
        print(f"ERROR: exports directory not found: {EXPORTS_DIR}")
        print("Run: bash /mnt/d/Projects/claude-hermes-ai-research-scaffold/scripts/export_to_cpds.sh")
        return None

    files = sorted(EXPORTS_DIR.glob("*.md"), reverse=True)
    if not files:
        print("No digest files found in exports directory.")
        return None

    if date_filter:
        files = [f for f in files if date_filter in f.name]
        if not files:
            print(f"No digest files found matching date: {date_filter}")
            return None

    return files[0]


def extract_layer1(content: str) -> str:
    """Extract Layer 1 (above the --- separator) from a digest."""
    parts = content.split("\n---\n")
    return parts[0].strip() if parts else content.strip()


def strip_source_appendix(content: str) -> str:
    """Remove source appendix tables — too verbose for newsletter."""
    return re.sub(r"## Source appendix.*", "", content, flags=re.DOTALL).strip()


def format_draft(source_file: Path, layer1: str) -> str:
    """Wrap Layer 1 content in newsletter draft template."""
    date_str  = datetime.now().strftime("%B %d, %Y")
    issue_date = datetime.now().strftime("%Y-%m-%d")

    return f"""---
issue_date: {issue_date}
source_digest: {source_file.name}
status: draft
---

# CPDS-AI Weekly — {date_str}

> **Editor note:** Review clusters below. Keep top 3. Add 1-2 sentences of
> your own context under each. Delete anything weak or off-vertical.
> Target: 350-400 words total above the fold.

---

{layer1}

---

## Subscribe / Share

If this was useful, forward it to one person building in this space.

[Subscribe to CPDS-AI]({{substack_url}})

---
*CPDS-AI surfaces demand signals from Reddit, newsletters, YouTube, and the web.
Automated daily. Curated weekly. Built on EMIS.*
"""


def write_draft(draft: str, dry_run: bool) -> None:
    """Write draft to content/drafts/ or print to stdout."""
    if dry_run:
        print(draft)
        return

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    date_slug = datetime.now().strftime("%Y-%m-%d")
    out_path  = DRAFTS_DIR / f"{date_slug}.md"

    if out_path.exists():
        print(f"Draft already exists: {out_path}")
        print("Delete it or use --date to curate a different digest.")
        sys.exit(1)

    out_path.write_text(draft, encoding="utf-8")
    print(f"Draft written: {out_path}")
    print("Next: review and edit, then run scripts/publish.py")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Curate EMIS digest into newsletter draft.")
    parser.add_argument("--date", default=None, help="Filter by date string e.g. 20260614")
    parser.add_argument("--dry-run", action="store_true", help="Print draft to stdout")
    args = parser.parse_args()

    source = find_latest_digest(args.date)
    if source is None:
        sys.exit(1)

    print(f"Source: {source.name}")
    content = source.read_text(encoding="utf-8")
    layer1  = extract_layer1(content)
    layer1  = strip_source_appendix(layer1)
    draft   = format_draft(source, layer1)

    write_draft(draft, args.dry_run)


if __name__ == "__main__":
    main()

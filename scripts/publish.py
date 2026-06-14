#!/usr/bin/env python3
"""publish.py — Push a curated draft to Substack. PLACEHOLDER — not yet wired.

This script is a placeholder. Wire it up once:
  1. Substack publication is created
  2. SUBSTACK_API_KEY and SUBSTACK_PUBLICATION_ID are in .env
  3. Vertical is confirmed and first draft is approved

Usage (future):
    python scripts/publish.py --draft content/drafts/2026-06-21.md
    python scripts/publish.py --draft content/drafts/2026-06-21.md --dry-run
"""
from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR   = PROJECT_ROOT / "content" / "drafts"
PUBLISHED_DIR = PROJECT_ROOT / "content" / "published"


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish draft to Substack.")
    parser.add_argument("--draft", required=True, help="Path to draft .md file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"ERROR: draft not found: {draft_path}")
        raise SystemExit(1)

    print("publish.py is a placeholder — Substack API not yet wired.")
    print(f"Draft ready at: {draft_path}")
    print("")
    print("Manual publish steps until this is wired:")
    print("  1. Open Substack dashboard")
    print("  2. Create new post")
    print("  3. Paste content from draft file")
    print("  4. Send to list")
    print("  5. Move draft to content/published/ manually")
    print("")
    print("To wire Substack API:")
    print("  - Add SUBSTACK_API_KEY to .env")
    print("  - Add SUBSTACK_PUBLICATION_ID to .env")
    print("  - Implement POST /api/v1/posts in this file")


if __name__ == "__main__":
    main()

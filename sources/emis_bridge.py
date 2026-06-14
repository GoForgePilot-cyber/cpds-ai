"""
EMIS Bridge — reads the EMIS export drop zone and parses the weekly digest.
READ ONLY. Never writes to or modifies anything under the EMIS paths.
Data flows: EMIS → /mnt/d/Projects/emis-exports/digest/ → this bridge → CPDS-AI
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EMIS_DIGEST_PATH = Path(os.getenv("EMIS_DIGEST_PATH", "/mnt/d/Projects/emis-exports/digest"))


def _find_latest_export() -> Path | None:
    """Find the most recent export file in the EMIS drop zone."""
    if not EMIS_DIGEST_PATH.exists():
        print(f"[emis_bridge] Drop zone not found: {EMIS_DIGEST_PATH}")
        return None

    # Support .md, .json, and .txt exports
    candidates = list(EMIS_DIGEST_PATH.glob("*.md")) + \
                 list(EMIS_DIGEST_PATH.glob("*.json")) + \
                 list(EMIS_DIGEST_PATH.glob("*.txt"))

    if not candidates:
        print("[emis_bridge] No export files found in drop zone")
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def _parse_markdown_digest(content: str) -> list[dict]:
    """
    Parse a markdown digest file from EMIS.
    EMIS digests are structured markdown with signal sections.
    This parser is tolerant — handles varying EMIS output formats.
    """
    signals = []

    # Try to extract numbered signal items (common EMIS format)
    # Pattern: "1. **Signal title** — description" or "## Signal: title"
    patterns = [
        r"#+\s+Signal[:\s]+(.+?)(?:\n|$)",
        r"\d+\.\s+\*{1,2}(.+?)\*{1,2}[:\s—–]+(.+?)(?:\n\n|\n#+|\Z)",
        r"###\s+(.+?)\n(.+?)(?=\n###|\Z)",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            description = match.group(2).strip() if match.lastindex >= 2 else ""
            if len(title) > 5:  # basic quality filter
                signals.append({
                    "id": f"emis_{hash(title) % 100000}",
                    "title": title,
                    "description": description[:500],
                    "source": "emis",
                    "signal_type": "synthesized_intelligence",
                    "score": 100 - (i * 5),  # preserve EMIS ranking order
                    "date": datetime.utcnow().isoformat(),
                    "url": "",
                })
        if signals:
            break  # stop at first pattern that works

    return signals


def _parse_json_digest(content: str) -> list[dict]:
    """Parse a JSON export from EMIS."""
    try:
        data = json.loads(content)
        signals = []
        # Handle list or dict with signals key
        items = data if isinstance(data, list) else data.get("signals", data.get("items", []))
        for i, item in enumerate(items):
            signals.append({
                "id": f"emis_{item.get('id', hash(str(item)) % 100000)}",
                "title": item.get("title", item.get("signal", item.get("name", ""))),
                "description": item.get("description", item.get("summary", item.get("content", ""))),
                "score": item.get("score", item.get("confidence", 100 - i * 5)),
                "source": "emis",
                "signal_type": "synthesized_intelligence",
                "date": item.get("date", datetime.utcnow().isoformat()),
                "url": item.get("url", item.get("source_url", "")),
                "emis_metadata": {k: v for k, v in item.items()
                                  if k not in ("title", "description", "score", "url", "date")},
            })
        return signals
    except Exception as e:
        print(f"[emis_bridge] JSON parse error: {e}")
        return []


def fetch() -> list[dict]:
    """
    Main entry point. Read latest EMIS export and return structured signals.
    Returns empty list (not error) if no export available — other sources continue.
    """
    latest = _find_latest_export()
    if not latest:
        print("[emis_bridge] No EMIS export available — continuing without EMIS signals")
        return []

    print(f"[emis_bridge] Reading EMIS export: {latest.name}")

    try:
        content = latest.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[emis_bridge] Failed to read export: {e}")
        return []

    # Parse based on file type
    if latest.suffix == ".json":
        signals = _parse_json_digest(content)
    else:
        signals = _parse_markdown_digest(content)

    # If parsing failed entirely, return the raw content as a single signal
    if not signals and content.strip():
        signals = [{
            "id": "emis_raw",
            "title": f"EMIS Weekly Digest — {latest.name}",
            "description": content[:2000],
            "score": 100,
            "source": "emis",
            "signal_type": "synthesized_intelligence",
            "date": datetime.utcnow().isoformat(),
            "url": "",
            "note": "raw_unparsed",
        }]

    print(f"[emis_bridge] Parsed {len(signals)} EMIS signals from {latest.name}")
    return signals

"""
curate.py — CPDS-AI core draft generator.

Version: 1.3.0
Last updated: 2026-06-15
Changelog:
  1.0.0 - 2026-06-15 - Initial release
  1.0.1 - 2026-06-15 - Fixed JSON truncation, added _safe_json_parse, increased max_tokens to 4000
  1.1.0 - 2026-06-15 - Switched to two-post model (free post + paid post separately)
  1.2.0 - 2026-06-15 - Changed title format from "Issue #N — Title" to "Jun 15 · Title"
  1.3.0 - 2026-06-15 - Removed source attribution from prompts (no HN/GitHub/EMIS references in output)

Reads weekly_signals.json from source_runner output.
Makes TWO separate Claude API calls:
  1. Free post: descriptive — what's happening (sent to all subscribers)
  2. Paid post: prescriptive — what to do about it (sent to paid subscribers only)

Title format: "Jun 15 · [Headline]" — no issue numbers.
Source attribution: never expose underlying sources (HN, GitHub, Reddit, EMIS) in output.
"""

import os
import sys
import json
import re
import yaml
from datetime import datetime
from pathlib import Path

import anthropic
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.beehiiv_publisher import push_draft

SIGNALS_PATH = PROJECT_ROOT / "sources" / "weekly_signals.json"
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
DRAFTS_DIR = PROJECT_ROOT / "drafts"
DRAFTS_DIR.mkdir(exist_ok=True)

CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

SUBSCRIBE_URL = "https://your-newsletter.beehiiv.com/subscribe"


def _date_abbrev(dt: datetime) -> str:
    """Returns abbreviated date format e.g. 'Jun 15'"""
    return dt.strftime("%b %-d")


def _load_signals() -> dict:
    if not SIGNALS_PATH.exists():
        raise FileNotFoundError(
            f"weekly_signals.json not found at {SIGNALS_PATH}\n"
            "Run source_runner.py first."
        )
    return json.loads(SIGNALS_PATH.read_text())


def _load_vertical() -> dict:
    with open(CONFIG_DIR / "vertical.yml") as f:
        return yaml.safe_load(f)


def _signals_summary(signals: list[dict], max_signals: int = 15) -> str:
    lines = []
    for i, sig in enumerate(signals[:max_signals]):
        source = sig.get("source", "unknown")
        title = sig.get("title", "")
        description = sig.get("description", "")[:200]
        score = sig.get("weighted_score", sig.get("score", 0))
        signal_type = sig.get("signal_type", "")
        lines.append(
            f"{i+1}. [{source.upper()} | {signal_type} | score:{score:.0f}]\n"
            f"   Title: {title}\n"
            f"   Context: {description}"
        )
    return "\n\n".join(lines)


def _safe_json_parse(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    try:
        truncated = raw.rstrip()
        last_complete = re.sub(r',?\s*"[^"]*"\s*:\s*[^,\}]*$', '', truncated)
        if not last_complete.endswith("}"):
            last_complete = last_complete.rstrip(",") + "\n}"
        return json.loads(last_complete)
    except Exception:
        pass

    print("[curate] WARNING: JSON parse failed — returning minimal paid section")
    return {
        "full_analysis": "Analysis generation failed — rerun curate.py to retry.",
        "commercial_layer": "",
        "fiverr_signals": [],
        "upwork_signals": [],
        "hiring_signals": [],
        "specific_opportunity": "Retry required.",
        "why_now": "",
        "who_this_is_for": "",
        "how_to_act": "",
        "launches_watching": [],
        "actionable_template_intro": "",
        "actionable_template_content": "",
        "actionable_template_usage": "",
        "next_week_watch": [],
    }


def _call_claude_free_section(signals_summary: str, vertical: dict, now: datetime) -> dict:
    vertical_name = vertical.get("display_name") or vertical.get("vertical_name") or "automation and AI tools"
    tagline = vertical.get("tagline") or "demand intelligence for builders"
    date_abbrev = _date_abbrev(now)

    prompt = f"""You are the editor of a paid weekly newsletter called CPDS-AI covering {vertical_name}.
Your audience: builders, operators, and founders who build or sell in this space.
Newsletter positioning: {tagline}

Write the FREE POST for this week. Title format: "{date_abbrev} · [6-8 word headline describing this week's theme]"
Do NOT use "Issue #" anywhere. The date prefix handles sequencing.

CRITICAL SOURCE RULE: Never mention or reference where signals came from.
Do NOT name: Hacker News, HN, GitHub, Reddit, forums, EMIS, or any specific platform.
Quotes are attributed to practitioner roles only — e.g. "— an AI infrastructure founder" or "— a senior ML engineer".
Signal sources are presented as original intelligence from our engine, not aggregated links.

The free post must:
- Feel genuinely valuable — not a tease of nothing
- Describe what's happening, NOT what to do about it (that's the paid post)
- Include 3 specific signals with concrete context (1-2 sentences each) — no source links
- Include 1 "what's moving" stat or trend with real numbers where available
- Include 2-3 practitioner quotes attributed to roles, not platforms
- End with a brief non-apologetic line pointing to the paid post
- Include 1 genuinely useful free resource (URL is fine — that's a deliberate recommendation)

Keep all string values concise — under 200 characters each.

This week's signals:
{signals_summary}

Respond with ONLY valid JSON, no markdown fences, no explanation:
{{
  "issue_date_abbrev": "{date_abbrev}",
  "issue_headline": "[6-8 word headline — no date prefix, that's added by the template]",
  "issue_title": "{date_abbrev} · [same 6-8 word headline — used for Beehiiv post title]",
  "signal_count": 6,
  "signal_snapshot": [
    {{"title": "...", "context": "1-2 sentences max — no source attribution"}}
  ],
  "whats_moving_stat": "One stat with a number — under 100 chars",
  "whats_moving_context": "1-2 sentences max",
  "community_pulse": [
    {{"text": "Quote under 150 chars", "source": "role-based attribution e.g. 'an AI agency operator' or 'a senior LLM engineer'"}}
  ],
  "paid_post_teaser": "One sentence under 120 chars",
  "free_resource_title": "Resource name",
  "free_resource_url": "https://...",
  "free_resource_context": "1 sentence",
  "subscribe_url": "{SUBSCRIBE_URL}"
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return _safe_json_parse(response.content[0].text)


def _call_claude_paid_section(signals_summary: str, vertical: dict, free_data: dict) -> dict:
    vertical_name = vertical.get("display_name") or vertical.get("vertical_name") or "automation and AI tools"
    issue_title = free_data.get("issue_title", "")

    prompt = f"""You are the editor of a paid weekly newsletter covering {vertical_name}.
Paying readers want actionable intelligence. Deliver the verdict, not summaries.

This week's theme: {issue_title}

The free post covered what signals appeared. Your job: synthesize what they mean and deliver one specific opportunity.

CRITICAL SOURCE RULE: Never mention where signals came from.
Do NOT name: Hacker News, HN, GitHub, Reddit, forums, EMIS, or any specific platform.
All intelligence is presented as original analysis from our signal engine.
Quotes attributed to practitioner roles only — not to specific platforms or threads.

This week's signals:
{signals_summary}

IMPORTANT: Keep all string values concise. No essays inside JSON strings.
Full analysis: max 4 short paragraphs. Each paragraph under 200 chars.
Specific opportunity: max 3 short paragraphs.
Actionable template content: max 300 chars.

Respond with ONLY valid JSON, no markdown fences, no explanation:
{{
  "full_analysis": "Why these signals matter together — 3-4 short paragraphs separated by \\n\\n",
  "commercial_layer": "What buyers are spending on — 2 short paragraphs separated by \\n\\n",
  "fiverr_signals": ["gig trend 1 under 100 chars", "gig trend 2 under 100 chars"],
  "upwork_signals": ["job pattern 1 under 100 chars"],
  "hiring_signals": ["hiring signal 1 under 100 chars"],
  "specific_opportunity": "What to build/pitch/position — 2-3 short paragraphs separated by \\n\\n",
  "why_now": "1-2 sentences under 200 chars",
  "who_this_is_for": "Specific role under 100 chars",
  "how_to_act": "3-4 steps separated by \\n",
  "launches_watching": [
    {{
      "name": "Name under 60 chars",
      "description": "One sentence under 120 chars",
      "editorial_take": "One sentence under 150 chars",
      "url": "https://..."
    }}
  ],
  "actionable_template_intro": "1 sentence under 100 chars",
  "actionable_template_content": "The template text under 300 chars",
  "actionable_template_usage": "1 sentence under 120 chars",
  "next_week_watch": [
    {{"topic": "Topic under 60 chars", "reason": "Reason under 120 chars"}}
  ]
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    return _safe_json_parse(response.content[0].text)


def _render_templates(free_data: dict, paid_data: dict) -> tuple[str, str]:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    free_md = env.get_template("free_section.md.j2").render(**free_data)
    paid_md = env.get_template("paid_section.md.j2").render(**paid_data)
    return free_md, paid_md


def _get_issue_number() -> int:
    existing = list(DRAFTS_DIR.glob("????-??-??_*_free.md"))
    return len(existing) + 1


def run():
    print(f"\n{'='*60}")
    print(f"CPDS-AI curate.py v1.3.0 — {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    now = datetime.utcnow()
    signals_data = _load_signals()
    vertical = _load_vertical()
    signals = signals_data.get("signals", [])

    if not signals:
        print("No signals found in weekly_signals.json — run source_runner.py first")
        return

    print(f"[curate] Loaded {len(signals)} signals")
    print(f"[curate] Vertical: {vertical.get('vertical_name', 'pending')}")
    print(f"[curate] Date: {_date_abbrev(now)}\n")

    signals_summary = _signals_summary(signals)

    print("[curate] Generating free post via Claude API...")
    free_data = _call_claude_free_section(signals_summary, vertical, now)
    print(f"[curate] Free post: '{free_data.get('issue_title', '')}'")

    print("[curate] Generating paid post via Claude API...")
    paid_data = _call_claude_paid_section(signals_summary, vertical, free_data)
    print("[curate] Paid post generated")

    free_md, paid_md = _render_templates(free_data, paid_data)

    date_str = now.strftime("%Y-%m-%d")
    free_path = DRAFTS_DIR / f"{date_str}_free.md"
    paid_path = DRAFTS_DIR / f"{date_str}_paid.md"
    free_path.write_text(free_md, encoding="utf-8")
    paid_path.write_text(paid_md, encoding="utf-8")
    print(f"[curate] Local drafts saved: {date_str}_free.md / {date_str}_paid.md")

    print("[curate] Pushing both drafts to Beehiiv...")
    try:
        result = push_draft(
            title=free_data.get("issue_title", f"{_date_abbrev(now)} · Demand signals"),
            subtitle=free_data.get("whats_moving_stat", "")[:150],
            free_md=free_md,
            paid_md=paid_md,
            preview_text=free_data.get("whats_moving_stat", "")[:90],
        )

        print(f"\n{'='*60}")
        print(f"✓ Both drafts ready for review")
        print(f"\n  FREE POST (all subscribers):")
        print(f"  {result['free'].get('draft_url')}")
        print(f"\n  PAID POST (paid subscribers only):")
        print(f"  {result['paid'].get('draft_url')}")
        print(f"\n  Title: {free_data.get('issue_title')}")
        print(f"{'='*60}")
        print(f"\nNext: review both drafts, edit (20-30 min total), send free post first then paid.")

        return result

    except Exception as e:
        print(f"\n[curate] Beehiiv push failed: {e}")
        print(f"  Free draft: {free_path}")
        print(f"  Paid draft: {paid_path}")
        return {"error": str(e)}


if __name__ == "__main__":
    run()

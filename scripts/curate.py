"""
curate.py — CPDS-AI core draft generator.

Reads weekly_signals.json from source_runner output.
Makes TWO separate Claude API calls:
  1. Free section: descriptive — what's happening
  2. Paid section: prescriptive — what to do about it

Renders Jinja2 templates with Claude's structured output.
Pushes completed draft to Beehiiv as 'draft' (never auto-sends).
Prints Beehiiv draft URL for human review.

Run every Sunday 6am via Task Scheduler (after source_runner Saturday 9pm).
"""

import os
import sys
import json
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

SUBSCRIBE_URL = "https://your-newsletter.beehiiv.com/subscribe"  # update after Beehiiv setup


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
    """Format top signals into a compact summary string for Claude prompts."""
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


def _call_claude_free_section(signals_summary: str, vertical: dict, issue_num: int) -> dict:
    """
    Claude API call 1: Generate free section content.
    Returns structured JSON with all template variables for free_section.md.j2
    """
    vertical_name = vertical.get("display_name") or vertical.get("vertical_name") or "automation and AI tools"
    tagline = vertical.get("tagline") or "demand intelligence for builders"

    prompt = f"""You are the editor of a paid weekly newsletter called CPDS-AI covering {vertical_name}.
Your audience: builders, operators, and founders who build or sell in this space.
Newsletter positioning: {tagline}

This is Issue #{issue_num}. Based on the signals below, write the FREE SECTION of this week's newsletter.

The free section must:
- Feel genuinely valuable — not a tease of nothing
- Describe what's happening, NOT what to do about it (that's paid)
- Include 3 specific signals with concrete context (not vague summaries)
- Include 1 "what's moving" stat or trend with real numbers where available
- Include 2-3 real practitioner quotes (synthesized from signal content — not invented)
- End with a brief, non-apologetic mention of what paid subscribers get
- Include 1 genuinely useful free resource relevant to this week's signals

This week's signals:
{signals_summary}

Respond with ONLY valid JSON, no markdown, no explanation:
{{
  "issue_title": "Issue #{issue_num} — [compelling 6-8 word description of this week's theme]",
  "issue_date": "{datetime.utcnow().strftime('%B %d, %Y')}",
  "issue_number": {issue_num},
  "signal_count": [number of sources checked],
  "signal_snapshot": [
    {{"title": "...", "context": "1-2 sentences of specific context", "url": "..."}}
    // exactly 3 items
  ],
  "whats_moving_stat": "One specific statistic or metric with a number",
  "whats_moving_context": "1-2 sentences explaining what this number means for the vertical",
  "community_pulse": [
    {{"text": "Direct quote or paraphrase from a practitioner", "source": "HN / n8n Forum / Reddit / etc"}}
    // 2-3 items
  ],
  "paid_preview": "One sentence about what paid subscribers got (no spoilers)",
  "free_resource_title": "Resource name",
  "free_resource_url": "https://...",
  "free_resource_context": "1 sentence on why it's useful this week",
  "subscribe_url": "{SUBSCRIBE_URL}"
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def _call_claude_paid_section(signals_summary: str, vertical: dict, free_data: dict) -> dict:
    """
    Claude API call 2: Generate paid section content.
    Returns structured JSON with all template variables for paid_section.md.j2
    This prompt is deliberately separate — different objective, different tone.
    """
    vertical_name = vertical.get("display_name") or vertical.get("vertical_name") or "automation and AI tools"
    issue_title = free_data.get("issue_title", "")

    prompt = f"""You are the editor of a paid weekly newsletter covering {vertical_name}.
Your paying readers are builders and operators who subscribe for actionable intelligence — not summaries.
They paid $19/month. Deliver the verdict, not just the signals.

This week's issue theme: {issue_title}

The free section already covered: what signals appeared this week.
Your job for the PAID SECTION: synthesize what they mean together and deliver one specific, actionable opportunity.

This week's signals:
{signals_summary}

Requirements:
- Full analysis must synthesize MULTIPLE signals — not just describe them individually
- Commercial layer: reference real buyer behavior (gig patterns, hiring signals, search trends)
- Specific opportunity: concrete, not vague. Name what to build/pitch/position. Not "explore AI tools."
- Actionable template: a real reusable thing (prompt, pricing model, outreach script, positioning framework)
- Next week watch: 3 specific things EMIS will monitor — tied to this week's themes

Respond with ONLY valid JSON, no markdown, no explanation:
{{
  "full_analysis": "3-4 paragraphs synthesizing why these signals matter TOGETHER — what pattern they reveal",
  "commercial_layer": "2-3 paragraphs on what buyers are spending money on — be specific",
  "fiverr_signals": ["specific gig trend 1", "specific gig trend 2"],
  "upwork_signals": ["specific job posting pattern 1"],
  "hiring_signals": ["specific LinkedIn hiring signal"],
  "specific_opportunity": "The specific thing to build, pitch, or position this week — 2-3 paragraphs",
  "why_now": "1-2 sentences on why this week specifically",
  "who_this_is_for": "Specific person/role this opportunity suits best",
  "how_to_act": "3-4 concrete steps to act on this opportunity",
  "launches_watching": [
    {{
      "name": "Product or repo name",
      "description": "What it does in one sentence",
      "editorial_take": "Why it matters for your vertical specifically",
      "url": "https://..."
    }}
    // 2-3 items
  ],
  "actionable_template_intro": "1 sentence introducing the template",
  "actionable_template_content": "The actual template text — prompt, script, framework, pricing model, etc.",
  "actionable_template_usage": "1-2 sentences on how to adapt and use it",
  "next_week_watch": [
    {{"topic": "Specific topic", "reason": "Why this will matter next week"}}
    // exactly 3 items
  ]
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def _render_templates(free_data: dict, paid_data: dict) -> tuple[str, str]:
    """Render both Jinja2 templates with Claude's output data."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    free_template = env.get_template("free_section.md.j2")
    paid_template = env.get_template("paid_section.md.j2")

    free_md = free_template.render(**free_data)
    paid_md = paid_template.render(**paid_data)

    return free_md, paid_md


def _get_issue_number() -> int:
    """Determine issue number from existing drafts."""
    existing = list(DRAFTS_DIR.glob("*.md"))
    return len(existing) + 1


def run():
    print(f"\n{'='*60}")
    print(f"CPDS-AI curate.py — {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    # Load inputs
    signals_data = _load_signals()
    vertical = _load_vertical()
    signals = signals_data.get("signals", [])
    issue_num = _get_issue_number()

    if not signals:
        print("⚠️  No signals found in weekly_signals.json")
        print("    Run source_runner.py first, or check source health logs")
        return

    print(f"[curate] Loaded {len(signals)} signals from {signals_data.get('generated_at', 'unknown time')}")
    print(f"[curate] Vertical: {vertical.get('vertical_name', 'pending selection')}")
    print(f"[curate] Issue #{issue_num}\n")

    signals_summary = _signals_summary(signals)

    # Claude API call 1: Free section
    print("[curate] Generating free section via Claude API...")
    free_data = _call_claude_free_section(signals_summary, vertical, issue_num)
    print(f"[curate] Free section: '{free_data.get('issue_title', '')}'")

    # Claude API call 2: Paid section
    print("[curate] Generating paid section via Claude API...")
    paid_data = _call_claude_paid_section(signals_summary, vertical, free_data)
    print("[curate] Paid section generated")

    # Render templates
    free_md, paid_md = _render_templates(free_data, paid_data)

    # Save local draft
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    draft_path = DRAFTS_DIR / f"{date_str}_issue_{issue_num:03d}.md"
    draft_content = f"<!-- FREE SECTION -->\n\n{free_md}\n\n<!-- PAYWALL BREAK -->\n\n<!-- PAID SECTION -->\n\n{paid_md}"
    draft_path.write_text(draft_content, encoding="utf-8")
    print(f"[curate] Local draft saved: {draft_path}")

    # Push to Beehiiv
    print("[curate] Pushing draft to Beehiiv...")
    try:
        result = push_draft(
            title=free_data.get("issue_title", f"Issue #{issue_num}"),
            subtitle=free_data.get("signal_snapshot", [{}])[0].get("context", "")[:150],
            free_md=free_md,
            paid_md=paid_md,
            preview_text=free_data.get("whats_moving_stat", "")[:90],
        )

        print(f"\n{'='*60}")
        print(f"✓ Draft ready for review")
        print(f"  Beehiiv draft URL: {result.get('draft_url')}")
        print(f"  Issue title: {free_data.get('issue_title')}")
        print(f"  Local draft: {draft_path}")
        print(f"{'='*60}\n")
        print("Next step: Open the Beehiiv draft URL, review and edit (20-30 min), then send.")

        return result

    except Exception as e:
        print(f"\n[curate] Beehiiv push failed: {e}")
        print(f"  Draft saved locally at: {draft_path}")
        print("  Check BEEHIIV_API_KEY and BEEHIIV_PUB_ID in .env")
        return {"local_draft": str(draft_path), "error": str(e)}


if __name__ == "__main__":
    run()

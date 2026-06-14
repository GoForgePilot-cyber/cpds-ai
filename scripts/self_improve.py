"""
self_improve.py — CPDS-AI Recursive Self-Improvement Engine

Triggered:
  - At every phase milestone (run by Claude Code as part of session end protocol)
  - When source health degrades (auto-triggered by source_runner)
  - Manually: python scripts/self_improve.py

What it does:
  1. Reads all source health logs, session logs, analytics history, milestone reports
  2. Calls Claude API with a structured analysis prompt
  3. Writes improvement report to analysis/improvement_YYYY-MM-DD.md
  4. Proposes specific, bounded changes
  5. Applies safe auto-changes (config updates, keyword lists)
  6. Flags changes requiring human approval

Self-improvement rules (from CLAUDE.md):
  CAN auto-change: prompt templates, source filters, keyword lists, output formatting, scheduling
  NEEDS approval: new paid sources (cost), free/paid split changes, pricing/platform changes
  NEVER changes: EMIS isolation, business model core, pricing without explicit instruction
"""

import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ANALYSIS_DIR = PROJECT_ROOT / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"
SOURCES_DIR = PROJECT_ROOT / "sources"
DRAFTS_DIR = PROJECT_ROOT / "drafts"

CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


def _gather_context() -> dict:
    """Collect all available data for analysis."""
    ctx = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_health": {},
        "analytics_history": [],
        "session_logs": [],
        "draft_count": 0,
        "milestone_reports": [],
        "vertical_status": "unknown",
        "signals_data": {},
    }

    # Source health
    health_path = LOGS_DIR / "source_health.json"
    if health_path.exists():
        ctx["source_health"] = json.loads(health_path.read_text())

    # Analytics history
    analytics_path = LOGS_DIR / "analytics_history.json"
    if analytics_path.exists():
        ctx["analytics_history"] = json.loads(analytics_path.read_text())[-12:]  # last 12 weeks

    # Session logs (last 5)
    sessions_dir = LOGS_DIR / "sessions"
    if sessions_dir.exists():
        session_files = sorted(sessions_dir.glob("session_*.md"), reverse=True)[:5]
        for sf in session_files:
            ctx["session_logs"].append({"file": sf.name, "content": sf.read_text()[:1000]})

    # Draft count
    ctx["draft_count"] = len(list(DRAFTS_DIR.glob("????-??-??_issue_*.md")))

    # Milestone reports
    for report in sorted(ANALYSIS_DIR.glob("milestone_*.md"), reverse=True)[:3]:
        ctx["milestone_reports"].append({"file": report.name, "content": report.read_text()[:1500]})

    # Vertical
    vertical_path = CONFIG_DIR / "vertical.yml"
    if vertical_path.exists():
        v = yaml.safe_load(vertical_path.read_text())
        ctx["vertical_status"] = v.get("status", "unknown")

    # Latest signals
    signals_path = SOURCES_DIR / "weekly_signals.json"
    if signals_path.exists():
        data = json.loads(signals_path.read_text())
        ctx["signals_data"] = {
            "generated_at": data.get("generated_at"),
            "total_output": data.get("total_output", 0),
            "by_source": {},
        }
        for sig in data.get("signals", []):
            src = sig.get("source", "unknown")
            ctx["signals_data"]["by_source"][src] = ctx["signals_data"]["by_source"].get(src, 0) + 1

    return ctx


def _call_claude_analysis(ctx: dict, trigger: str) -> dict:
    """Call Claude API for self-improvement analysis."""
    prompt = f"""You are the recursive self-improvement engine for CPDS-AI, a paid weekly newsletter business.
Your job: honest, actionable analysis of what's working, what isn't, and what should change.
No validation. No filler. If something is broken or drifting, say so directly.

Trigger for this analysis: {trigger}
Timestamp: {ctx['timestamp']}
Issues published so far: {ctx['draft_count']}
Vertical status: {ctx['vertical_status']}

SOURCE HEALTH:
{json.dumps(ctx['source_health'], indent=2)[:3000]}

ANALYTICS (last 12 weeks):
{json.dumps(ctx['analytics_history'], indent=2)[:2000]}

SIGNALS BREAKDOWN (latest run):
{json.dumps(ctx['signals_data'], indent=2)}

RECENT SESSION LOGS:
{json.dumps([s['content'] for s in ctx['session_logs']], indent=2)[:2000]}

MILESTONE REPORTS:
{json.dumps([r['content'] for r in ctx['milestone_reports']], indent=2)[:2000]}

Analyze along these dimensions and respond with ONLY valid JSON:
{{
  "executive_summary": "3-4 sentences — honest state of the business. What's working, what's failing, what the number one issue is right now.",

  "source_health_assessment": {{
    "healthy_sources": ["sources performing well with specific reasons"],
    "degraded_sources": ["sources underperforming with specific reasons"],
    "dead_sources": ["sources that should be disabled — explain why"],
    "recommended_additions": ["new sources to add — must justify ROI vs effort"]
  }},

  "content_quality_assessment": {{
    "signal_density": "Is the signal volume adequate for quality output? Specific numbers.",
    "prompt_drift": "Are Claude prompts producing generic summaries or genuine intelligence? Evidence?",
    "free_paid_split_effectiveness": "Is the split driving upgrades or giving away too much?",
    "recommended_prompt_changes": ["specific prompt improvement 1", "specific prompt improvement 2"]
  }},

  "business_viability": {{
    "growth_trajectory": "On track / behind / ahead vs. target — with specific numbers",
    "paid_conversion_trend": "Direction and projection",
    "churn_signals": "Any early warning signs",
    "months_to_50_paid": "Realistic estimate based on current trajectory",
    "viability_verdict": "viable / at_risk / needs_pivot",
    "viability_rationale": "Why — be specific"
  }},

  "idea_audit": {{
    "dead_ideas": [
      {{"idea": "what was planned", "why_dead": "what the data shows"}}
    ],
    "better_ideas": [
      {{"idea": "what emerged from data", "evidence": "specific signal or metric that supports it"}}
    ],
    "new_opportunities": [
      {{"opportunity": "what wasn't in the original plan", "source": "where this came from", "effort": "low/medium/high"}}
    ]
  }},

  "auto_apply_changes": [
    {{
      "type": "config_change | prompt_change | keyword_update | source_disable | source_enable",
      "description": "What to change",
      "rationale": "Why",
      "file": "which file to change",
      "change": "the specific change to make"
    }}
  ],

  "approval_needed": [
    {{
      "change": "What needs human approval",
      "reason_needs_approval": "Why this can't be auto-applied",
      "recommendation": "What you recommend the human decide"
    }}
  ],

  "next_30_days": "3 specific, prioritized actions for the next 30 days. Not vague. Each should have a clear owner and success metric."
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def _apply_safe_changes(analysis: dict) -> list[str]:
    """Apply changes that are within auto-apply rules. Returns list of applied changes."""
    applied = []
    auto_changes = analysis.get("auto_apply_changes", [])

    for change in auto_changes:
        change_type = change.get("type", "")
        description = change.get("description", "")
        file_path = change.get("file", "")
        change_detail = change.get("change", "")

        # Only apply config/keyword changes automatically
        if change_type in ("config_change", "keyword_update", "source_disable", "source_enable"):
            try:
                target = PROJECT_ROOT / file_path
                if target.exists() and target.suffix in (".yml", ".yaml", ".json"):
                    # Log what would be changed — actual changes require Claude Code
                    applied.append(f"[FLAGGED FOR CLAUDE CODE] {change_type}: {description}")
                else:
                    applied.append(f"[SKIPPED] Target file not found: {file_path}")
            except Exception as e:
                applied.append(f"[ERROR] Failed to apply {description}: {e}")
        else:
            applied.append(f"[NEEDS REVIEW] {change_type}: {description}")

    return applied


def _write_report(analysis: dict, ctx: dict, trigger: str, applied_changes: list[str]) -> Path:
    """Write improvement report to analysis/."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d-%H%M")
    report_path = ANALYSIS_DIR / f"improvement_{date_str}.md"

    lines = [
        f"# Self-Improvement Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        f"**Trigger:** {trigger}",
        f"**Issues published:** {ctx['draft_count']}",
        f"**Vertical:** {ctx['vertical_status']}",
        "",
        "---",
        "",
        "## Executive summary",
        "",
        analysis.get("executive_summary", "No summary generated"),
        "",
        "---",
        "",
        "## Source health",
        "",
        "**Healthy:**",
    ]

    for s in analysis.get("source_health_assessment", {}).get("healthy_sources", []):
        lines.append(f"- {s}")

    lines.extend(["", "**Degraded:**"])
    for s in analysis.get("source_health_assessment", {}).get("degraded_sources", []):
        lines.append(f"- ⚠️ {s}")

    lines.extend(["", "**Dead / disable:**"])
    for s in analysis.get("source_health_assessment", {}).get("dead_sources", []):
        lines.append(f"- ✕ {s}")

    lines.extend(["", "**Recommended additions:**"])
    for s in analysis.get("source_health_assessment", {}).get("recommended_additions", []):
        lines.append(f"- ➕ {s}")

    viability = analysis.get("business_viability", {})
    lines.extend([
        "",
        "---",
        "",
        "## Business viability",
        "",
        f"**Verdict:** {viability.get('viability_verdict', 'unknown').upper()}",
        f"**Growth:** {viability.get('growth_trajectory', '')}",
        f"**Paid conversion trend:** {viability.get('paid_conversion_trend', '')}",
        f"**Months to 50 paid:** {viability.get('months_to_50_paid', '?')}",
        f"**Rationale:** {viability.get('viability_rationale', '')}",
        "",
        "---",
        "",
        "## Idea audit",
        "",
        "### Dead ideas (data contradicts the plan)",
    ])

    for item in analysis.get("idea_audit", {}).get("dead_ideas", []):
        lines.append(f"- **{item.get('idea')}** — {item.get('why_dead')}")

    lines.extend(["", "### Better ideas (emerged from data)"])
    for item in analysis.get("idea_audit", {}).get("better_ideas", []):
        lines.append(f"- **{item.get('idea')}** — evidence: {item.get('evidence')}")

    lines.extend(["", "### New opportunities (not in original plan)"])
    for item in analysis.get("idea_audit", {}).get("new_opportunities", []):
        lines.append(f"- **{item.get('opportunity')}** [{item.get('effort')} effort] — {item.get('source')}")

    lines.extend([
        "",
        "---",
        "",
        "## Changes applied automatically",
    ])
    for c in applied_changes:
        lines.append(f"- {c}")

    lines.extend([
        "",
        "## Changes needing human approval",
    ])
    for item in analysis.get("approval_needed", []):
        lines.extend([
            f"",
            f"**{item.get('change')}**",
            f"Why approval needed: {item.get('reason_needs_approval')}",
            f"Recommendation: {item.get('recommendation')}",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Next 30 days",
        "",
        analysis.get("next_30_days", "No recommendations generated"),
        "",
        "---",
        "",
        f"*Generated by self_improve.py at {ctx['timestamp']}*",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run(trigger: str = "manual") -> Path:
    """Main entry point."""
    print(f"\n{'='*60}")
    print(f"CPDS-AI Self-Improvement Engine — {datetime.utcnow().isoformat()}")
    print(f"Trigger: {trigger}")
    print(f"{'='*60}\n")

    print("[self_improve] Gathering project context...")
    ctx = _gather_context()

    print("[self_improve] Calling Claude API for analysis...")
    analysis = _call_claude_analysis(ctx, trigger)

    print("[self_improve] Applying safe auto-changes...")
    applied = _apply_safe_changes(analysis)

    print("[self_improve] Writing improvement report...")
    report_path = _write_report(analysis, ctx, trigger, applied)

    # Print summary
    viability = analysis.get("business_viability", {})
    print(f"\n── Self-Improvement Report ──")
    print(f"  Viability verdict: {viability.get('viability_verdict', '?').upper()}")
    print(f"  Executive summary: {analysis.get('executive_summary', '')[:200]}...")
    print(f"  Dead ideas found: {len(analysis.get('idea_audit', {}).get('dead_ideas', []))}")
    print(f"  New opportunities: {len(analysis.get('idea_audit', {}).get('new_opportunities', []))}")
    print(f"  Changes needing approval: {len(analysis.get('approval_needed', []))}")
    print(f"\n  Full report: {report_path}")
    print(f"\n  ⚠️  Claude.ai (architect) should review this report before next session.")

    return report_path


if __name__ == "__main__":
    trigger = sys.argv[1] if len(sys.argv) > 1 else "manual"
    run(trigger)

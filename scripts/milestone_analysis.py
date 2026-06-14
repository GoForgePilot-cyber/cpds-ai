"""
milestone_analysis.py — Deep-dive viability analysis at phase milestones.

More thorough than self_improve.py — this is the strategic business review.
Run at end of each phase. Output is read by Claude.ai (architect) for decisions.

Usage: python scripts/milestone_analysis.py --phase 1
"""

import os
import sys
import json
import yaml
import argparse
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

# What was expected at each phase (from original research and plan)
PHASE_BENCHMARKS = {
    1: {
        "description": "7-day build sprint complete",
        "expected_outputs": [
            "Full source ingestion pipeline running",
            "curate.py generating drafts",
            "Beehiiv on Scale plan configured",
            "Free/paid split working",
            "Task Scheduler automating weekly pipeline",
            "Social post generator working",
        ],
        "no_subscriber_target": True,  # pre-launch, no subscribers expected
    },
    2: {
        "description": "Vertical selected, first real issues published",
        "subscriber_target": 50,
        "open_rate_target": 0.40,
        "paid_target": 0,
        "weeks_elapsed": 4,
    },
    3: {
        "description": "Commercial sources live, consistent publishing",
        "subscriber_target": 200,
        "open_rate_target": 0.42,
        "paid_target": 5,
        "weeks_elapsed": 8,
    },
    4: {
        "description": "First issue published, community engagement active",
        "subscriber_target": 400,
        "open_rate_target": 0.42,
        "paid_target": 15,
        "weeks_elapsed": 12,
    },
    5: {
        "description": "Newsletter swaps and sponsor outreach active",
        "subscriber_target": 800,
        "open_rate_target": 0.43,
        "paid_target": 30,
        "weeks_elapsed": 20,
    },
    6: {
        "description": "50 paid subscribers — flip to paid model",
        "subscriber_target": 1670,
        "open_rate_target": 0.43,
        "paid_target": 50,
        "weeks_elapsed": 30,
    },
}


def _gather_full_context(phase: int) -> dict:
    """Gather comprehensive context for milestone analysis."""
    ctx = {
        "phase": phase,
        "timestamp": datetime.utcnow().isoformat(),
        "benchmarks": PHASE_BENCHMARKS.get(phase, {}),
        "source_health": {},
        "analytics_history": [],
        "session_logs": [],
        "all_improvement_reports": [],
        "draft_count": 0,
        "vertical_config": {},
        "signals_history": [],
    }

    # Source health
    health_path = LOGS_DIR / "source_health.json"
    if health_path.exists():
        ctx["source_health"] = json.loads(health_path.read_text())

    # Full analytics history
    analytics_path = LOGS_DIR / "analytics_history.json"
    if analytics_path.exists():
        ctx["analytics_history"] = json.loads(analytics_path.read_text())

    # All session logs
    sessions_dir = LOGS_DIR / "sessions"
    if sessions_dir.exists():
        for sf in sorted(sessions_dir.glob("session_*.md"), reverse=True)[:10]:
            ctx["session_logs"].append(sf.read_text()[:800])

    # All previous improvement reports
    for report in sorted(ANALYSIS_DIR.glob("improvement_*.md"), reverse=True)[:5]:
        ctx["all_improvement_reports"].append(report.read_text()[:1000])

    ctx["draft_count"] = len(list(DRAFTS_DIR.glob("????-??-??_issue_*.md")))

    # Vertical config
    vertical_path = CONFIG_DIR / "vertical.yml"
    if vertical_path.exists():
        ctx["vertical_config"] = yaml.safe_load(vertical_path.read_text())

    return ctx


def _call_claude_milestone(ctx: dict) -> dict:
    """Deep-dive milestone analysis via Claude API."""
    phase = ctx["phase"]
    benchmarks = ctx["benchmarks"]

    prompt = f"""You are the strategic advisor for CPDS-AI, a paid weekly newsletter business.
This is a MILESTONE ANALYSIS at the end of Phase {phase}: "{benchmarks.get('description', '')}".

Your job: honest, thorough business review. This report is read by the human owner to make strategic decisions.
No validation. No filler. Identify drift, dead ends, and real opportunities.

PHASE {phase} BENCHMARKS:
{json.dumps(benchmarks, indent=2)}

ACTUAL STATE:
- Issues published: {ctx['draft_count']}
- Source health: {json.dumps(ctx['source_health'], indent=2)[:2000]}
- Analytics history: {json.dumps(ctx['analytics_history'], indent=2)[:2000]}
- Vertical config: {json.dumps(ctx['vertical_config'], indent=2)[:500]}

PRIOR IMPROVEMENT REPORTS (summary):
{chr(10).join(ctx['all_improvement_reports'][:3])[:2000]}

Respond with ONLY valid JSON:
{{
  "phase_verdict": {{
    "status": "complete | partial | failed",
    "completion_percentage": 0-100,
    "what_was_delivered": ["item 1", "item 2"],
    "what_was_not_delivered": ["item 1"],
    "blocking_issues": ["anything that prevented full completion"]
  }},

  "business_health": {{
    "overall": "healthy | concerning | at_risk | pivoting",
    "narrative": "3-4 sentences. Honest. What is the actual state of this business right now?",
    "strongest_signals": ["what's working with specifics"],
    "weakest_points": ["what's failing with specifics"],
    "trajectory": "accelerating | stable | decelerating | stalled"
  }},

  "drift_analysis": {{
    "strategy_drift": "Has the strategy drifted from the original plan? In what ways? Is drift good or bad?",
    "audience_drift": "Is the actual audience different from the intended audience? Should strategy adjust?",
    "content_drift": "Is content quality / positioning drifting? Evidence?",
    "monetization_drift": "Is the path to revenue on track or drifting?"
  }},

  "idea_audit": {{
    "confirmed_dead": [
      {{"idea": "...", "evidence": "specific data point that kills it", "what_to_do_instead": "..."}}
    ],
    "confirmed_working": [
      {{"idea": "...", "evidence": "specific data showing it works", "double_down": true}}
    ],
    "upgraded_ideas": [
      {{"original": "what was planned", "better_version": "what data suggests instead", "rationale": "..."}}
    ],
    "new_ideas": [
      {{"idea": "emerged from phase data", "evidence": "...", "risk": "low/medium/high", "potential": "low/medium/high"}}
    ]
  }},

  "competitive_assessment": {{
    "new_entrants": "Have new newsletters / tools launched in the vertical this phase?",
    "incumbent_changes": "Has any incumbent strengthened or weakened?",
    "market_shift": "Has the vertical itself changed enough to reconsider selection?",
    "moat_assessment": "What's your actual defensible advantage right now?"
  }},

  "phase_next_plan": {{
    "priority_1": {{"action": "...", "owner": "Claude Code | User | Both", "success_metric": "...", "deadline": "..."}},
    "priority_2": {{"action": "...", "owner": "...", "success_metric": "...", "deadline": "..."}},
    "priority_3": {{"action": "...", "owner": "...", "success_metric": "...", "deadline": "..."}},
    "kill_criteria": "If X doesn't happen by Y date, we should Z. Be specific.",
    "pivot_trigger": "At what point should the vertical or strategy be reconsidered? Be specific."
  }},

  "honest_assessment": "One paragraph. No softening. What does the owner most need to hear right now that they might not want to hear?"
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def _write_milestone_report(phase: int, analysis: dict, ctx: dict) -> Path:
    """Write the milestone analysis report."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    report_path = ANALYSIS_DIR / f"milestone_phase{phase}_{date_str}.md"

    verdict = analysis.get("phase_verdict", {})
    health = analysis.get("business_health", {})
    drift = analysis.get("drift_analysis", {})
    ideas = analysis.get("idea_audit", {})
    competitive = analysis.get("competitive_assessment", {})
    next_plan = analysis.get("phase_next_plan", {})

    lines = [
        f"# Milestone Analysis — Phase {phase}",
        f"**Date:** {date_str}",
        f"**Phase:** {PHASE_BENCHMARKS.get(phase, {}).get('description', '')}",
        f"**Issues published:** {ctx['draft_count']}",
        "",
        "---",
        "",
        "## Phase verdict",
        "",
        f"**Status:** {verdict.get('status', '?').upper()}",
        f"**Completion:** {verdict.get('completion_percentage', '?')}%",
        "",
        "**Delivered:**",
    ]
    for item in verdict.get("what_was_delivered", []):
        lines.append(f"- ✓ {item}")

    lines.extend(["", "**Not delivered:**"])
    for item in verdict.get("what_was_not_delivered", []):
        lines.append(f"- ✗ {item}")

    if verdict.get("blocking_issues"):
        lines.extend(["", "**Blockers:**"])
        for item in verdict.get("blocking_issues", []):
            lines.append(f"- ⚠️ {item}")

    lines.extend([
        "",
        "---",
        "",
        "## Business health",
        "",
        f"**Overall:** {health.get('overall', '?').upper()}",
        f"**Trajectory:** {health.get('trajectory', '?')}",
        "",
        health.get("narrative", ""),
        "",
        "**Strongest signals:**",
    ])
    for s in health.get("strongest_signals", []):
        lines.append(f"- ✓ {s}")

    lines.extend(["", "**Weakest points:**"])
    for s in health.get("weakest_points", []):
        lines.append(f"- ✗ {s}")

    lines.extend([
        "",
        "---",
        "",
        "## Drift analysis",
        "",
        f"**Strategy drift:** {drift.get('strategy_drift', '')}",
        "",
        f"**Audience drift:** {drift.get('audience_drift', '')}",
        "",
        f"**Content drift:** {drift.get('content_drift', '')}",
        "",
        f"**Monetization drift:** {drift.get('monetization_drift', '')}",
        "",
        "---",
        "",
        "## Idea audit",
        "",
        "### Confirmed dead",
    ])
    for item in ideas.get("confirmed_dead", []):
        lines.extend([
            f"**✗ {item.get('idea')}**",
            f"Evidence: {item.get('evidence')}",
            f"Instead: {item.get('what_to_do_instead')}",
            "",
        ])

    lines.append("### Confirmed working")
    for item in ideas.get("confirmed_working", []):
        lines.extend([
            f"**✓ {item.get('idea')}**",
            f"Evidence: {item.get('evidence')}",
            "",
        ])

    lines.append("### Upgraded ideas")
    for item in ideas.get("upgraded_ideas", []):
        lines.extend([
            f"**Original:** {item.get('original')}",
            f"**Better:** {item.get('better_version')}",
            f"Rationale: {item.get('rationale')}",
            "",
        ])

    lines.append("### New ideas (not in original plan)")
    for item in ideas.get("new_ideas", []):
        lines.extend([
            f"**{item.get('idea')}** [risk: {item.get('risk')} | potential: {item.get('potential')}]",
            f"Evidence: {item.get('evidence')}",
            "",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Competitive assessment",
        "",
        f"**New entrants:** {competitive.get('new_entrants', '')}",
        "",
        f"**Incumbent changes:** {competitive.get('incumbent_changes', '')}",
        "",
        f"**Market shift:** {competitive.get('market_shift', '')}",
        "",
        f"**Your moat:** {competitive.get('moat_assessment', '')}",
        "",
        "---",
        "",
        "## Phase next plan",
        "",
        "**Priority 1:**",
        f"Action: {next_plan.get('priority_1', {}).get('action', '')}",
        f"Owner: {next_plan.get('priority_1', {}).get('owner', '')}",
        f"Success: {next_plan.get('priority_1', {}).get('success_metric', '')}",
        f"By: {next_plan.get('priority_1', {}).get('deadline', '')}",
        "",
        "**Priority 2:**",
        f"Action: {next_plan.get('priority_2', {}).get('action', '')}",
        f"Owner: {next_plan.get('priority_2', {}).get('owner', '')}",
        f"Success: {next_plan.get('priority_2', {}).get('success_metric', '')}",
        f"By: {next_plan.get('priority_2', {}).get('deadline', '')}",
        "",
        "**Priority 3:**",
        f"Action: {next_plan.get('priority_3', {}).get('action', '')}",
        f"Owner: {next_plan.get('priority_3', {}).get('owner', '')}",
        f"Success: {next_plan.get('priority_3', {}).get('success_metric', '')}",
        f"By: {next_plan.get('priority_3', {}).get('deadline', '')}",
        "",
        f"**Kill criteria:** {next_plan.get('kill_criteria', '')}",
        f"**Pivot trigger:** {next_plan.get('pivot_trigger', '')}",
        "",
        "---",
        "",
        "## Honest assessment",
        "",
        f"*{analysis.get('honest_assessment', '')}*",
        "",
        "---",
        "",
        f"*Generated by milestone_analysis.py at {ctx['timestamp']}*",
        f"*Read by Claude.ai (architect) before Phase {phase + 1} begins*",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run(phase: int) -> Path:
    """Main entry point."""
    print(f"\n{'='*60}")
    print(f"CPDS-AI Milestone Analysis — Phase {phase}")
    print(f"'{PHASE_BENCHMARKS.get(phase, {}).get('description', '')}'")
    print(f"{'='*60}\n")

    print("[milestone] Gathering comprehensive context...")
    ctx = _gather_full_context(phase)

    print("[milestone] Running deep-dive analysis via Claude API...")
    analysis = _call_claude_milestone(ctx)

    print("[milestone] Writing milestone report...")
    report_path = _write_milestone_report(phase, analysis, ctx)

    # Print key verdicts
    verdict = analysis.get("phase_verdict", {})
    health = analysis.get("business_health", {})
    next_plan = analysis.get("phase_next_plan", {})

    print(f"\n── Milestone Phase {phase} ──")
    print(f"  Phase status: {verdict.get('status', '?').upper()}")
    print(f"  Business health: {health.get('overall', '?').upper()}")
    print(f"  Trajectory: {health.get('trajectory', '?')}")
    print(f"  Dead ideas: {len(analysis.get('idea_audit', {}).get('confirmed_dead', []))}")
    print(f"  New ideas: {len(analysis.get('idea_audit', {}).get('new_ideas', []))}")
    print(f"  Kill criteria: {next_plan.get('kill_criteria', 'none set')[:100]}")
    print(f"\n  Full report: {report_path}")
    print(f"\n  ⚠️  Review this report in Claude.ai before starting Phase {phase + 1}")

    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CPDS-AI Milestone Analysis")
    parser.add_argument("--phase", type=int, required=True, help="Phase number to analyze (1-6)")
    args = parser.parse_args()
    run(args.phase)

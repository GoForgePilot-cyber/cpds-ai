"""
analytics_digest.py — pulls weekly Beehiiv subscriber and engagement stats.
Writes a 10-line summary to logs/analytics_YYYY-MM-DD.md.
Flags metrics that are below benchmark thresholds.
Run every Monday 8am via Task Scheduler.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.beehiiv_publisher import get_analytics, get_subscriber_stats

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

ANALYTICS_PATH = LOGS_DIR / "analytics_history.json"

# Benchmark thresholds from market research
BENCHMARKS = {
    "open_rate_target": 0.40,       # 40% — niche B2B target
    "paid_conversion_target": 0.03, # 3% — realistic median
    "monthly_churn_max": 0.05,      # 5% — acceptable ceiling
    "weekly_growth_min": 0,         # at least 0 net new subscribers
}


def _load_history() -> list:
    if ANALYTICS_PATH.exists():
        return json.loads(ANALYTICS_PATH.read_text())
    return []


def _save_history(history: list):
    ANALYTICS_PATH.write_text(json.dumps(history, indent=2))


def _flag(metric: str, value: float, target: float, higher_is_better: bool = True) -> str:
    if higher_is_better:
        ok = value >= target
    else:
        ok = value <= target
    symbol = "✓" if ok else "⚠️"
    return f"{symbol} {metric}: {value:.1%} (target: {target:.1%})"


def run():
    print(f"\n── CPDS-AI Analytics Digest — {datetime.utcnow().strftime('%Y-%m-%d')} ──\n")

    stats = get_subscriber_stats()
    recent_posts = get_analytics(limit=4)

    total_subs = stats.get("total_subscribers", 0)
    active_subs = stats.get("active_subscribers", 0)
    paid_subs = stats.get("total_paid", 0)

    # Calculate metrics
    paid_rate = (paid_subs / active_subs) if active_subs > 0 else 0

    # Load history for trend calculation
    history = _load_history()
    prev_total = history[-1].get("total_subscribers", total_subs) if history else total_subs
    net_growth = total_subs - prev_total

    # Post-level metrics from recent issues
    avg_open_rate = 0
    if recent_posts:
        open_rates = [p.get("stats", {}).get("open_rate", 0) for p in recent_posts if p.get("stats")]
        avg_open_rate = sum(open_rates) / len(open_rates) if open_rates else 0

    # Build report
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        f"# Analytics Digest — {date_str}",
        "",
        "## Subscriber snapshot",
        f"  Total: {total_subs:,}",
        f"  Active: {active_subs:,}",
        f"  Paid: {paid_subs:,}",
        f"  Net growth this week: {net_growth:+,}",
        "",
        "## Health flags",
        _flag("Open rate (avg last 4 issues)", avg_open_rate, BENCHMARKS["open_rate_target"]),
        _flag("Paid conversion rate", paid_rate, BENCHMARKS["paid_conversion_target"]),
        f"  Weekly net growth: {net_growth:+,} (target: >{BENCHMARKS['weekly_growth_min']})",
        "",
        "## Distance to milestones",
        f"  Paid subscribers: {paid_subs}/50 needed for paid flip ({max(0, 50 - paid_subs)} remaining)",
        f"  Free subscribers: {total_subs} total",
        "",
        "## Recent issues",
    ]

    for post in recent_posts[:4]:
        post_stats = post.get("stats", {})
        lines.append(
            f"  - {post.get('title', 'Untitled')[:50]}: "
            f"open {post_stats.get('open_rate', 0):.1%}, "
            f"clicks {post_stats.get('click_rate', 0):.1%}"
        )

    # Flags
    flags = []
    if avg_open_rate > 0 and avg_open_rate < BENCHMARKS["open_rate_target"]:
        flags.append(f"Open rate {avg_open_rate:.1%} is below {BENCHMARKS['open_rate_target']:.0%} target — review subject lines and send timing")
    if paid_rate < BENCHMARKS["paid_conversion_target"] and paid_subs > 0:
        flags.append(f"Paid conversion {paid_rate:.1%} is below {BENCHMARKS['paid_conversion_target']:.0%} benchmark — review paywall CTA copy")
    if net_growth <= 0 and total_subs > 0:
        flags.append("Net subscriber growth is flat or negative — increase community posting frequency")

    if flags:
        lines.extend(["", "## Action flags"])
        for flag in flags:
            lines.append(f"  ⚠️  {flag}")
    else:
        lines.extend(["", "  ✓ All metrics within range"])

    report = "\n".join(lines)

    # Save report
    report_path = LOGS_DIR / f"analytics_{date_str}.md"
    report_path.write_text(report, encoding="utf-8")

    # Save to history for trend tracking
    history.append({
        "date": date_str,
        "total_subscribers": total_subs,
        "active_subscribers": active_subs,
        "paid_subscribers": paid_subs,
        "avg_open_rate": avg_open_rate,
        "paid_conversion_rate": paid_rate,
        "net_growth": net_growth,
    })
    _save_history(history[-52:])  # keep 1 year of weekly data

    print(report)
    print(f"\n  Saved to: {report_path}")
    return report


if __name__ == "__main__":
    run()

"""
Source Runner — orchestrates all enabled sources, deduplicates signals,
tracks source health, and writes the weekly_signals.json used by curate.py.

Run every Saturday 9pm via Task Scheduler.
"""

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sources import hn_source, github_source, forum_source, trends_source
from sources import devto_source, producthunt_source, emis_bridge

CONFIG_DIR = PROJECT_ROOT / "config"
SOURCES_DIR = PROJECT_ROOT / "sources"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SIGNALS_OUTPUT = SOURCES_DIR / "weekly_signals.json"
SEEN_IDS_PATH = SOURCES_DIR / "seen_ids.json"
HEALTH_LOG_PATH = LOGS_DIR / "source_health.json"


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _load_seen_ids() -> set:
    if SEEN_IDS_PATH.exists():
        data = json.loads(SEEN_IDS_PATH.read_text())
        # Clean out IDs older than dedup_window_days
        cutoff = datetime.utcnow().timestamp() - (14 * 86400)
        return {k for k, v in data.items() if v > cutoff}
    return set()


def _save_seen_ids(seen: dict):
    SEEN_IDS_PATH.write_text(json.dumps(seen, indent=2))


def _deduplicate(signals: list[dict], seen_ids: set) -> tuple[list[dict], set]:
    """Remove signals seen in the dedup window. Returns (new_signals, updated_seen_ids)."""
    fresh = []
    now = datetime.utcnow().timestamp()
    new_seen = {sid: ts for sid, ts in zip(seen_ids, [now]*len(seen_ids))}

    for signal in signals:
        sid = signal.get("id", "")
        if sid and sid not in seen_ids:
            fresh.append(signal)
            new_seen[sid] = now

    return fresh, new_seen


def _apply_weights(signals: list[dict], source_config: dict) -> list[dict]:
    """Apply source weights to signal scores for ranking."""
    for signal in signals:
        source = signal.get("source", "")
        weight = source_config.get(source, {}).get("weight", 1.0)
        signal["weighted_score"] = signal.get("score", 0) * weight
    return signals


def _track_health(source_name: str, result_count: int, error: str | None, config: dict):
    """Log source health for self-improvement analysis."""
    health = {}
    if HEALTH_LOG_PATH.exists():
        health = json.loads(HEALTH_LOG_PATH.read_text())

    if source_name not in health:
        health[source_name] = {"runs": [], "consecutive_empty": 0}

    run = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": result_count,
        "error": error,
    }
    health[source_name]["runs"].append(run)
    health[source_name]["runs"] = health[source_name]["runs"][-20:]  # keep last 20

    threshold = config.get("health_threshold", {}).get("empty_runs_before_alert", 3)
    if result_count == 0:
        health[source_name]["consecutive_empty"] = health[source_name].get("consecutive_empty", 0) + 1
    else:
        health[source_name]["consecutive_empty"] = 0

    if health[source_name]["consecutive_empty"] >= threshold:
        health[source_name]["alert"] = f"Source has returned 0 results for {health[source_name]['consecutive_empty']} consecutive runs — investigate"

    HEALTH_LOG_PATH.write_text(json.dumps(health, indent=2))


def run():
    print(f"\n{'='*60}")
    print(f"CPDS-AI Source Runner — {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    # Load configs
    vertical = _load_yaml(CONFIG_DIR / "vertical.yml")
    sources_cfg = _load_yaml(CONFIG_DIR / "sources.yml").get("sources", {})

    if vertical.get("status") != "active":
        print("⚠️  vertical.yml status is not 'active' — using placeholder keywords")
        keywords = ["automation", "workflow", "AI tools", "SaaS", "billing"]
        github_topics = ["automation", "workflow-automation"]
        forum_urls = ["https://community.n8n.io"]
    else:
        keywords = vertical.get("keywords", [])
        github_topics = vertical.get("github_topics", [])
        forum_urls = vertical.get("forum_urls", ["https://community.n8n.io"])

    seen_ids = _load_seen_ids()
    seen_with_ts = {}  # for saving with timestamps

    all_signals = []

    # ── Run each source ────────────────────────────────────────────────────

    source_runs = [
        ("hacker_news",    lambda: hn_source.fetch(keywords, min_score=sources_cfg.get("hacker_news", {}).get("min_score", 50))),
        ("github",         lambda: github_source.fetch(github_topics, keywords, min_star_delta=sources_cfg.get("github", {}).get("min_star_delta", 25))),
        ("forum",          lambda: forum_source.fetch(forum_urls, keywords, min_replies=sources_cfg.get("n8n_forum", {}).get("min_replies", 3))),
        ("google_trends",  lambda: trends_source.fetch(keywords[:5])),
        ("devto",          lambda: devto_source.fetch(keywords, min_reactions=sources_cfg.get("devto", {}).get("min_reactions", 20))),
        ("emis_bridge",    lambda: emis_bridge.fetch()),
    ]

    # Add Product Hunt if enabled
    if sources_cfg.get("product_hunt", {}).get("enabled", False):
        ph_topics = vertical.get("producthunt_topics", [])
        source_runs.append(
            ("product_hunt", lambda: producthunt_source.fetch(ph_topics, keywords, min_votes=sources_cfg.get("product_hunt", {}).get("min_votes", 100)))
        )

    for source_name, source_fn in source_runs:
        cfg = sources_cfg.get(source_name, {})
        if not cfg.get("enabled", True):
            print(f"[runner] Skipping {source_name} (disabled in config)")
            continue

        print(f"\n[runner] Running {source_name}...")
        error = None
        results = []
        try:
            results = source_fn()
        except Exception as e:
            error = str(e)
            print(f"[runner] ERROR in {source_name}: {e}")

        _track_health(source_name, len(results), error, cfg)

        for signal in results:
            signal["source_config"] = source_name
        all_signals.extend(results)

    print(f"\n[runner] Total raw signals: {len(all_signals)}")

    # ── Deduplicate ────────────────────────────────────────────────────────
    fresh_signals, new_seen = _deduplicate(all_signals, seen_ids)
    seen_with_ts.update(new_seen)
    _save_seen_ids(seen_with_ts)
    print(f"[runner] After dedup (14-day window): {len(fresh_signals)} fresh signals")

    # ── Apply weights and rank ─────────────────────────────────────────────
    fresh_signals = _apply_weights(fresh_signals, sources_cfg)
    fresh_signals.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)

    # ── Cap and write output ───────────────────────────────────────────────
    max_signals = _load_yaml(CONFIG_DIR / "sources.yml").get("max_signals_per_run", 50)
    output_signals = fresh_signals[:max_signals]

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "vertical_status": vertical.get("status"),
        "vertical_name": vertical.get("vertical_name"),
        "total_raw": len(all_signals),
        "total_fresh": len(fresh_signals),
        "total_output": len(output_signals),
        "signals": output_signals,
    }

    SIGNALS_OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n[runner] Wrote {len(output_signals)} signals to {SIGNALS_OUTPUT}")

    # ── Summary ────────────────────────────────────────────────────────────
    by_source = {}
    for s in output_signals:
        src = s.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    print("\n── Signal breakdown by source ──")
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {src:<25} {count}")

    print(f"\n✓ Source runner complete — {datetime.utcnow().isoformat()}\n")
    return output


if __name__ == "__main__":
    run()

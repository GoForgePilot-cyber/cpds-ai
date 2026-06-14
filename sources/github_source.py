"""
GitHub source — monitors repo star velocity for vertical topics.
Stars gained per week is a clean adoption signal that precedes press coverage.
Persists last-week star counts to sources/github_stars.json for delta calculation.
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STARS_CACHE_PATH = Path(__file__).parent / "github_stars.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _load_star_cache() -> dict:
    if STARS_CACHE_PATH.exists():
        return json.loads(STARS_CACHE_PATH.read_text())
    return {}


def _save_star_cache(cache: dict):
    STARS_CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _search_repos_by_topic(topic: str, min_stars: int = 100) -> list[dict]:
    """Search GitHub repos by topic tag, filtered by minimum stars."""
    results = []
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            headers=_github_headers(),
            params={
                "q": f"topic:{topic} stars:>{min_stars}",
                "sort": "updated",
                "per_page": 20,
            },
            timeout=15,
        )
        resp.raise_for_status()
        for repo in resp.json().get("items", []):
            results.append({
                "id": str(repo["id"]),
                "name": repo["full_name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "language": repo.get("language", ""),
                "topic": topic,
                "updated_at": repo.get("updated_at", ""),
            })
        time.sleep(1.0)  # GitHub rate limit: 5000/hr authenticated, 60/hr unauth
    except Exception as e:
        print(f"[github_source] Error searching topic '{topic}': {e}")
    return results


def _search_repos_by_keyword(keyword: str, min_stars: int = 50, days_back: int = 30) -> list[dict]:
    """Search repos created or pushed to recently matching a keyword."""
    results = []
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            headers=_github_headers(),
            params={
                "q": f"{keyword} pushed:>{cutoff} stars:>{min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": 15,
            },
            timeout=15,
        )
        resp.raise_for_status()
        for repo in resp.json().get("items", []):
            results.append({
                "id": str(repo["id"]),
                "name": repo["full_name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "language": repo.get("language", ""),
                "topic": keyword,
                "updated_at": repo.get("updated_at", ""),
            })
        time.sleep(1.0)
    except Exception as e:
        print(f"[github_source] Error searching keyword '{keyword}': {e}")
    return results


def _calculate_deltas(repos: list[dict], cache: dict) -> list[dict]:
    """Attach star delta (change since last run) to each repo."""
    now = datetime.utcnow().isoformat()
    enriched = []
    for repo in repos:
        repo_id = repo["id"]
        prev_stars = cache.get(repo_id, {}).get("stars", repo["stars"])
        delta = repo["stars"] - prev_stars
        cache[repo_id] = {"stars": repo["stars"], "checked_at": now}
        repo["star_delta"] = delta
        enriched.append(repo)
    return enriched


def fetch(topics: list[str], keywords: list[str], min_star_delta: int = 25) -> list[dict]:
    """
    Main entry point. Fetch repos by topics and keywords, compute star velocity.
    Returns repos with star_delta >= min_star_delta, sorted by delta desc.
    """
    if not GITHUB_TOKEN:
        print("[github_source] WARNING: No GITHUB_TOKEN set — using unauthenticated (60 req/hr limit)")

    print("[github_source] Fetching GitHub repo signals...")
    cache = _load_star_cache()

    all_repos = []
    seen_ids = set()

    for topic in topics:
        for repo in _search_repos_by_topic(topic):
            if repo["id"] not in seen_ids:
                seen_ids.add(repo["id"])
                all_repos.append(repo)

    for keyword in keywords[:3]:  # limit keyword searches to avoid rate limits
        for repo in _search_repos_by_keyword(keyword):
            if repo["id"] not in seen_ids:
                seen_ids.add(repo["id"])
                all_repos.append(repo)

    enriched = _calculate_deltas(all_repos, cache)
    _save_star_cache(cache)

    # Filter and sort by delta
    filtered = [r for r in enriched if r["star_delta"] >= min_star_delta]
    filtered.sort(key=lambda x: x["star_delta"], reverse=True)

    # Attach source metadata
    for r in filtered:
        r["source"] = "github"
        r["signal_type"] = "repo_velocity"

    print(f"[github_source] Found {len(filtered)} repos with star delta >= {min_star_delta}")
    return filtered

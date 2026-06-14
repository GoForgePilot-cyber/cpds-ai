"""
Hacker News source — Firebase API (live feed) + Algolia API (keyword search)
Returns structured signal list filtered by vertical keywords and score threshold.
"""

import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def _algolia_search(terms: list[str], min_score: int, days_back: int = 7) -> list[dict]:
    """Search HN via Algolia full-text API for keyword-matched stories."""
    results = []
    cutoff = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())

    for term in terms:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": term,
                    "tags": "story",
                    "numericFilters": f"points>={min_score},created_at_i>{cutoff}",
                    "hitsPerPage": 20,
                },
                timeout=10,
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                results.append({
                    "id": hit.get("objectID"),
                    "title": hit.get("title", ""),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "score": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "type": _classify_hn_type(hit.get("title", "")),
                    "source": "hacker_news",
                    "date": hit.get("created_at", ""),
                    "matched_term": term,
                })
            time.sleep(0.5)  # rate limit courtesy
        except Exception as e:
            print(f"[hn_source] Algolia error for term '{term}': {e}")

    return results


def _firebase_feed(feed_type: str = "topstories", limit: int = 10) -> list[dict]:
    """Pull top/new/best stories from HN Firebase API."""
    results = []
    try:
        resp = requests.get(
            f"https://hacker-news.firebaseio.com/v0/{feed_type}.json",
            timeout=10,
        )
        resp.raise_for_status()
        story_ids = resp.json()[:limit]

        for story_id in story_ids:
            try:
                story_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=10,
                )
                story_resp.raise_for_status()
                story = story_resp.json()
                if story and story.get("type") == "story":
                    results.append({
                        "id": str(story.get("id")),
                        "title": story.get("title", ""),
                        "url": story.get("url") or f"https://news.ycombinator.com/item?id={story.get('id')}",
                        "score": story.get("score", 0),
                        "comments": story.get("descendants", 0),
                        "type": _classify_hn_type(story.get("title", "")),
                        "source": "hacker_news",
                        "date": datetime.utcfromtimestamp(story.get("time", 0)).isoformat(),
                        "matched_term": "top_feed",
                    })
                time.sleep(0.1)
            except Exception:
                continue
    except Exception as e:
        print(f"[hn_source] Firebase feed error: {e}")

    return results


def _classify_hn_type(title: str) -> str:
    """Classify HN post type from title prefix."""
    t = title.strip().lower()
    if t.startswith("show hn"):
        return "show_hn"
    if t.startswith("ask hn"):
        return "ask_hn"
    if t.startswith("who is hiring") or "hiring" in t[:20]:
        return "hiring"
    return "story"


def fetch(keywords: list[str], min_score: int = 50) -> list[dict]:
    """
    Main entry point. Fetch HN signals matching vertical keywords.
    Returns deduplicated list sorted by score desc.
    """
    print("[hn_source] Fetching Hacker News signals...")

    # Keyword search via Algolia
    keyword_results = _algolia_search(keywords, min_score)

    # Top feed for context (lower score threshold)
    top_results = [
        r for r in _firebase_feed("topstories", 30)
        if r["score"] >= min_score
    ]

    # Merge and deduplicate by story ID
    seen = set()
    merged = []
    for item in keyword_results + top_results:
        if item["id"] not in seen:
            seen.add(item["id"])
            merged.append(item)

    # Sort by score descending
    merged.sort(key=lambda x: x["score"], reverse=True)

    print(f"[hn_source] Found {len(merged)} signals")
    return merged

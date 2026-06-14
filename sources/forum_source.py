"""
Forum source — Discourse forums (n8n community, etc.) + Indie Hackers via Algolia.
Discourse exposes clean JSON endpoints without auth. IH uses their Algolia backend.
"""

import time
import requests
from datetime import datetime, timedelta


def _fetch_discourse_forum(base_url: str, min_replies: int = 3, max_results: int = 15) -> list[dict]:
    """
    Fetch top threads from a Discourse forum.
    base_url example: https://community.n8n.io
    """
    results = []
    try:
        resp = requests.get(
            f"{base_url}/top.json",
            params={"period": "weekly"},
            timeout=15,
            headers={"User-Agent": "CPDS-AI Signal Collector (newsletter research)"},
        )
        resp.raise_for_status()
        topics = resp.json().get("topic_list", {}).get("topics", [])

        for topic in topics[:max_results]:
            if topic.get("reply_count", 0) < min_replies:
                continue
            results.append({
                "id": f"discourse_{base_url.split('//')[1].split('.')[0]}_{topic['id']}",
                "title": topic.get("title", ""),
                "url": f"{base_url}/t/{topic.get('slug')}/{topic['id']}",
                "score": topic.get("like_count", 0) + topic.get("reply_count", 0) * 2,
                "replies": topic.get("reply_count", 0),
                "views": topic.get("views", 0),
                "source": "forum_discourse",
                "forum": base_url,
                "date": topic.get("last_posted_at", ""),
                "signal_type": "practitioner_discussion",
            })

        time.sleep(1.0)
    except Exception as e:
        print(f"[forum_source] Discourse error for {base_url}: {e}")

    return results


def _fetch_indie_hackers(keywords: list[str], max_results: int = 10) -> list[dict]:
    """
    Fetch Indie Hackers posts matching keywords via their Algolia search backend.
    IH uses Algolia for search — we POST directly to their index.
    """
    results = []
    cutoff_ts = int((datetime.utcnow() - timedelta(days=30)).timestamp())

    for keyword in keywords:
        try:
            resp = requests.post(
                "https://yfqs6uses0-dsn.algolia.net/1/indexes/prod_post_es/query",
                json={
                    "query": keyword,
                    "hitsPerPage": max_results,
                    "filters": f"createdAt > {cutoff_ts}",
                    "attributesToRetrieve": ["id", "title", "url", "commentCount", "votes", "createdAt"],
                },
                headers={
                    "X-Algolia-Application-Id": "YFQS6USES0",
                    "X-Algolia-API-Key": "8b35c26b5f9ba6d13c9f29d4e96bb748",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            resp.raise_for_status()

            for hit in resp.json().get("hits", []):
                results.append({
                    "id": f"ih_{hit.get('id', '')}",
                    "title": hit.get("title", ""),
                    "url": f"https://www.indiehackers.com{hit.get('url', '')}",
                    "score": hit.get("votes", 0) + hit.get("commentCount", 0),
                    "comments": hit.get("commentCount", 0),
                    "source": "indie_hackers",
                    "matched_term": keyword,
                    "date": datetime.utcfromtimestamp(hit.get("createdAt", 0)).isoformat() if hit.get("createdAt") else "",
                    "signal_type": "revenue_validation",
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"[forum_source] IH error for keyword '{keyword}': {e}")

    return results


def fetch(forum_urls: list[str], keywords: list[str], min_replies: int = 3) -> list[dict]:
    """
    Main entry point. Fetch signals from all configured Discourse forums + Indie Hackers.
    """
    print("[forum_source] Fetching forum signals...")
    results = []
    seen_ids = set()

    for url in forum_urls:
        for item in _fetch_discourse_forum(url, min_replies):
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                results.append(item)

    for item in _fetch_indie_hackers(keywords):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[forum_source] Found {len(results)} forum signals")
    return results

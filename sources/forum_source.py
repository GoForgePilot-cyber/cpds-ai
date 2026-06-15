"""
Forum source — Discourse forums (n8n community, etc.) + Indie Hackers via RSS.
Discourse exposes clean JSON endpoints without auth.
IH fetched via RSS feed — Algolia endpoint blocked by WSL DNS on some networks.
"""

import time
import feedparser
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


def _fetch_indie_hackers_rss(keywords: list[str], max_results: int = 20) -> list[dict]:
    """
    Fetch Indie Hackers posts via RSS feed and filter by keywords.
    RSS fallback — avoids Algolia DNS resolution issues on restricted networks.
    """
    results = []
    seen_ids = set()
    cutoff = datetime.utcnow() - timedelta(days=30)

    try:
        feed = feedparser.parse(
            "https://www.indiehackers.com/feed.rss",
            agent="CPDS-AI Signal Collector (newsletter research)",
        )

        for entry in feed.entries[:60]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = (title + " " + summary).lower()

            # Filter by keyword match
            matched = next((kw for kw in keywords if kw.lower() in combined), None)
            if not matched:
                continue

            # Date filter
            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6])
                if pub_dt < cutoff:
                    continue

            entry_id = f"ih_rss_{entry.get('id', hash(title))}"
            if entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)

            results.append({
                "id": entry_id,
                "title": title,
                "url": entry.get("link", ""),
                "score": 5,  # RSS has no vote count — flat score, ranked by recency
                "source": "indie_hackers",
                "matched_term": matched,
                "date": datetime(*published[:6]).isoformat() if published else "",
                "signal_type": "revenue_validation",
            })

            if len(results) >= max_results:
                break

    except Exception as e:
        print(f"[forum_source] IH RSS error: {e}")

    return results


def fetch(forum_urls: list[str], keywords: list[str], min_replies: int = 3) -> list[dict]:
    """
    Main entry point. Fetch signals from all configured Discourse forums + Indie Hackers RSS.
    """
    print("[forum_source] Fetching forum signals...")
    results = []
    seen_ids = set()

    for url in forum_urls:
        for item in _fetch_discourse_forum(url, min_replies):
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                results.append(item)

    for item in _fetch_indie_hackers_rss(keywords):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[forum_source] Found {len(results)} forum signals")
    return results

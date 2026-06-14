"""
Product Hunt source — GraphQL API (requires free developer token) with RSS fallback.
Launch traction = commercial demand signal weeks before press coverage.
"""

import os
import time
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

PH_API_KEY = os.getenv("PRODUCTHUNT_API_KEY")
PH_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"


def _fetch_via_graphql(topics: list[str], min_votes: int = 100, days_back: int = 7) -> list[dict]:
    """Fetch launches via Product Hunt GraphQL API filtered by topic."""
    if not PH_API_KEY:
        return []

    results = []
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for topic in topics:
        query = """
        query($topic: String!, $after: DateTime!) {
          posts(topic: $topic, after: $after, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node { name slug }
                  }
                }
              }
            }
          }
        }
        """
        try:
            resp = requests.post(
                PH_GRAPHQL_URL,
                json={"query": query, "variables": {"topic": topic, "after": cutoff}},
                headers={
                    "Authorization": f"Bearer {PH_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            edges = resp.json().get("data", {}).get("posts", {}).get("edges", [])

            for edge in edges:
                node = edge.get("node", {})
                if node.get("votesCount", 0) < min_votes:
                    continue
                results.append({
                    "id": f"ph_{node['id']}",
                    "title": f"{node.get('name', '')} — {node.get('tagline', '')}",
                    "url": node.get("url", ""),
                    "score": node.get("votesCount", 0),
                    "comments": node.get("commentsCount", 0),
                    "source": "product_hunt",
                    "topic": topic,
                    "date": node.get("createdAt", ""),
                    "signal_type": "launch_traction",
                })
            time.sleep(1.0)
        except Exception as e:
            print(f"[producthunt_source] GraphQL error for topic '{topic}': {e}")

    return results


def _fetch_via_rss(keywords: list[str]) -> list[dict]:
    """Fallback: fetch Product Hunt RSS feed and filter by keywords."""
    results = []
    try:
        feed = feedparser.parse("https://www.producthunt.com/feed")
        for entry in feed.entries[:50]:
            title = entry.get("title", "").lower()
            summary = entry.get("summary", "").lower()
            if any(kw.lower() in title or kw.lower() in summary for kw in keywords):
                results.append({
                    "id": f"ph_rss_{entry.get('id', hash(entry.get('title', '')))}",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "score": 0,  # RSS doesn't expose vote count
                    "source": "product_hunt",
                    "date": entry.get("published", ""),
                    "signal_type": "launch_traction",
                    "note": "via_rss_fallback",
                })
    except Exception as e:
        print(f"[producthunt_source] RSS fallback error: {e}")
    return results


def fetch(topics: list[str], keywords: list[str], min_votes: int = 100) -> list[dict]:
    """Main entry point."""
    if not PH_API_KEY:
        print("[producthunt_source] No PRODUCTHUNT_API_KEY — using RSS fallback")
        results = _fetch_via_rss(keywords)
    else:
        print("[producthunt_source] Fetching Product Hunt signals via GraphQL...")
        results = _fetch_via_graphql(topics, min_votes)
        if not results:
            print("[producthunt_source] GraphQL returned empty — falling back to RSS")
            results = _fetch_via_rss(keywords)

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[producthunt_source] Found {len(results)} Product Hunt signals")
    return results

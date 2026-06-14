"""
DEV.to source via Forem public API.
Practitioner articles reveal what problems people are solving and sharing.
High reaction count = widespread practitioner interest.
"""

import time
import requests
from datetime import datetime


def fetch(keywords: list[str], top_days: int = 7, min_reactions: int = 20, max_results: int = 10) -> list[dict]:
    """
    Fetch top DEV.to articles by tag matching vertical keywords.
    """
    print("[devto_source] Fetching DEV.to signals...")
    results = []
    seen_ids = set()

    for keyword in keywords:
        # Convert multi-word keywords to DEV.to tag format
        tag = keyword.lower().replace(" ", "").replace("-", "")

        try:
            resp = requests.get(
                "https://dev.to/api/articles",
                params={
                    "tag": tag,
                    "top": top_days,
                    "per_page": max_results,
                },
                headers={"User-Agent": "CPDS-AI Signal Collector (newsletter research)"},
                timeout=10,
            )
            resp.raise_for_status()

            for article in resp.json():
                if article.get("public_reactions_count", 0) < min_reactions:
                    continue
                article_id = f"devto_{article['id']}"
                if article_id in seen_ids:
                    continue
                seen_ids.add(article_id)

                results.append({
                    "id": article_id,
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "score": article.get("public_reactions_count", 0),
                    "comments": article.get("comments_count", 0),
                    "source": "devto",
                    "tag": tag,
                    "matched_keyword": keyword,
                    "date": article.get("published_at", ""),
                    "signal_type": "solution_pattern",
                    "description": article.get("description", ""),
                })

            time.sleep(0.5)

        except Exception as e:
            print(f"[devto_source] Error for tag '{tag}': {e}")

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[devto_source] Found {len(results)} DEV.to signals")
    return results

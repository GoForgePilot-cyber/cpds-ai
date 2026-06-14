"""
Google Trends source via pytrends.
Returns relative interest and rising queries for vertical keywords.
Not absolute volume — directional velocity only. Use to cross-validate other signals.
"""

import time
from datetime import datetime

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False


def fetch(keywords: list[str], timeframe: str = "today 1-m") -> list[dict]:
    """
    Fetch Google Trends data for vertical keywords.
    Returns rising queries and interest summary per keyword group.
    """
    if not PYTRENDS_AVAILABLE:
        print("[trends_source] pytrends not installed — skipping")
        return []

    print("[trends_source] Fetching Google Trends signals...")
    results = []

    # Process keywords in groups of 5 (pytrends limit)
    for i in range(0, min(len(keywords), 10), 5):
        batch = keywords[i:i+5]
        try:
            pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
            pytrends.build_payload(batch, timeframe=timeframe, geo="")
            time.sleep(2.0)  # mandatory delay to avoid rate limiting

            # Interest over time
            interest_df = pytrends.interest_over_time()
            if not interest_df.empty:
                for kw in batch:
                    if kw in interest_df.columns:
                        recent = interest_df[kw].tail(4).mean()  # last 4 weeks avg
                        peak = interest_df[kw].max()
                        results.append({
                            "id": f"trends_{kw.replace(' ', '_')}",
                            "title": f"Trend: {kw}",
                            "url": f"https://trends.google.com/trends/explore?q={kw.replace(' ', '+')}",
                            "score": int(recent),
                            "peak_interest": int(peak),
                            "recent_avg": round(float(recent), 1),
                            "source": "google_trends",
                            "keyword": kw,
                            "date": datetime.utcnow().isoformat(),
                            "signal_type": "demand_velocity",
                        })

            # Rising related queries
            time.sleep(2.0)
            related = pytrends.related_queries()
            for kw in batch:
                kw_data = related.get(kw, {})
                rising = kw_data.get("rising")
                if rising is not None and not rising.empty:
                    top_rising = rising.head(3)
                    for _, row in top_rising.iterrows():
                        query = row.get("query", "")
                        value = row.get("value", 0)
                        if query and value:
                            results.append({
                                "id": f"trends_rising_{query.replace(' ', '_')}",
                                "title": f"Rising search: '{query}' (related to {kw})",
                                "url": f"https://trends.google.com/trends/explore?q={query.replace(' ', '+')}",
                                "score": min(int(value), 100),
                                "source": "google_trends",
                                "keyword": kw,
                                "rising_query": query,
                                "date": datetime.utcnow().isoformat(),
                                "signal_type": "rising_query",
                            })

            time.sleep(3.0)  # between batches

        except Exception as e:
            print(f"[trends_source] Error for batch {batch}: {e}")
            time.sleep(5.0)  # back off on error

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"[trends_source] Found {len(results)} trend signals")
    return results

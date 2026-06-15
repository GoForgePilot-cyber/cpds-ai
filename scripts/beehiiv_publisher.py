"""
Beehiiv Publisher — pushes two separate draft posts to Beehiiv:
  1. Free post — sent to all subscribers
  2. Paid post — sent to paid subscribers only (audience filter)

Both always created as 'draft'. Human reviews and sends both before Sunday deadline.
"""

import os
import requests
import markdown as md_lib
from dotenv import load_dotenv

load_dotenv()

BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY")
BEEHIIV_PUB_ID = os.getenv("BEEHIIV_PUB_ID")
BEEHIIV_BASE_URL = "https://api.beehiiv.com/v2"


def _markdown_to_html(md_text: str) -> str:
    return md_lib.markdown(md_text, extensions=["extra", "nl2br"])


def _post_draft(title: str, subtitle: str, html: str, preview_text: str, audience: str) -> dict:
    """
    Push a single draft post to Beehiiv.
    audience: "all" for free post, "premium" for paid post.
    """
    if not BEEHIIV_API_KEY or not BEEHIIV_PUB_ID:
        raise ValueError("BEEHIIV_API_KEY and BEEHIIV_PUB_ID must be set in .env")

    payload = {
        "title": title,
        "subtitle": subtitle,
        "preview_text": preview_text[:90],
        "content_json": {
            "type": "doc",
            "content": [
                {
                    "type": "rawHtml",
                    "attrs": {"html": html}
                }
            ]
        },
        "status": "draft",
        "audience": audience,
        "email_capture_disabled": False,
    }

    resp = requests.post(
        f"{BEEHIIV_BASE_URL}/publications/{BEEHIIV_PUB_ID}/posts",
        json=payload,
        headers={
            "Authorization": f"Bearer {BEEHIIV_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(
            f"Beehiiv API error {resp.status_code}: {resp.text}"
        )

    data = resp.json().get("data", {})
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "web_url": data.get("web_url"),
        "draft_url": f"https://app.beehiiv.com/p/{data.get('id')}/edit",
    }


def push_draft(
    title: str,
    subtitle: str,
    free_md: str,
    paid_md: str,
    preview_text: str = "",
) -> dict:
    """
    Push two draft posts to Beehiiv:
      - Free post: all subscribers
      - Paid post: paid subscribers only

    Returns dict with draft URLs for both posts.
    """
    free_html = _markdown_to_html(free_md)
    paid_html = _markdown_to_html(paid_md)

    issue_num = title.split("#")[1].split("—")[0].strip() if "#" in title else ""
    paid_title = f"[Paid] {title}"
    paid_preview = f"This week's full analysis, opportunity, and actionable template — Issue #{issue_num}"

    print("[beehiiv] Pushing free post (all subscribers)...")
    free_result = _post_draft(
        title=title,
        subtitle=subtitle,
        html=free_html,
        preview_text=preview_text or subtitle[:90],
        audience="all",
    )

    print("[beehiiv] Pushing paid post (paid subscribers only)...")
    paid_result = _post_draft(
        title=paid_title,
        subtitle="Full analysis + opportunity + actionable template",
        html=paid_html,
        preview_text=paid_preview[:90],
        audience="premium",
    )

    return {
        "free": free_result,
        "paid": paid_result,
    }


def get_analytics(limit: int = 10) -> list[dict]:
    if not BEEHIIV_API_KEY or not BEEHIIV_PUB_ID:
        return []
    try:
        resp = requests.get(
            f"{BEEHIIV_BASE_URL}/publications/{BEEHIIV_PUB_ID}/posts",
            params={"limit": limit, "status": "confirmed"},
            headers={"Authorization": f"Bearer {BEEHIIV_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print(f"[beehiiv_publisher] Analytics fetch error: {e}")
        return []


def get_subscriber_stats() -> dict:
    if not BEEHIIV_API_KEY or not BEEHIIV_PUB_ID:
        return {}
    try:
        resp = requests.get(
            f"{BEEHIIV_BASE_URL}/publications/{BEEHIIV_PUB_ID}",
            headers={"Authorization": f"Bearer {BEEHIIV_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "total_subscribers": data.get("stats", {}).get("total_subscribers", 0),
            "active_subscribers": data.get("stats", {}).get("active_subscribers", 0),
            "total_paid": data.get("stats", {}).get("total_paid_subscribers", 0),
        }
    except Exception as e:
        print(f"[beehiiv_publisher] Subscriber stats error: {e}")
        return {}

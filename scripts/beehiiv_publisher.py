"""
Beehiiv Publisher — pushes formatted newsletter drafts to Beehiiv via REST API.
Always creates as 'draft' — human reviews before sending.
Handles paywall break insertion between free and paid sections.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY")
BEEHIIV_PUB_ID = os.getenv("BEEHIIV_PUB_ID")
BEEHIIV_BASE_URL = "https://api.beehiiv.com/v2"


def _markdown_to_html(md_text: str) -> str:
    """Convert markdown to basic HTML for Beehiiv body_content field."""
    import markdown as md_lib
    return md_lib.markdown(md_text, extensions=["extra", "nl2br"])


def _build_blocks(free_html: str, paid_html: str) -> list[dict]:
    """
    Build Beehiiv block structure with paywall break between free and paid sections.
    Uses Beehiiv's block API format.
    """
    blocks = [
        {
            "type": "html",
            "html": free_html,
        },
        {
            "type": "paywall_break",
            # Beehiiv will render the configured paywall CTA here automatically
        },
        {
            "type": "html",
            "html": paid_html,
        },
    ]
    return blocks


def push_draft(
    title: str,
    subtitle: str,
    free_md: str,
    paid_md: str,
    preview_text: str = "",
) -> dict:
    """
    Push a draft post to Beehiiv. Returns API response including draft URL.

    Args:
        title: Post title (e.g. "Issue #3 — What's driving n8n adoption this week")
        subtitle: Subtitle shown in email preview
        free_md: Markdown content for free section (shown to all subscribers)
        paid_md: Markdown content for paid section (gated by paywall break)
        preview_text: Email preview text (first 90 chars shown in inbox)

    Returns:
        dict with 'id', 'url', and 'web_url' from Beehiiv API
    """
    if not BEEHIIV_API_KEY or not BEEHIIV_PUB_ID:
        raise ValueError(
            "BEEHIIV_API_KEY and BEEHIIV_PUB_ID must be set in .env\n"
            "API key: Beehiiv dashboard → Settings → API\n"
            "Publication ID: visible in dashboard URL"
        )

    free_html = _markdown_to_html(free_md)
    paid_html = _markdown_to_html(paid_md)
    blocks = _build_blocks(free_html, paid_html)

    payload = {
        "title": title,
        "subtitle": subtitle,
        "preview_text": preview_text or subtitle[:90],
        "blocks": blocks,
        "status": "draft",  # NEVER change this to 'confirmed' — human reviews first
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
            f"Beehiiv API error {resp.status_code}: {resp.text}\n"
            "Check your API key and publication ID in .env"
        )

    data = resp.json().get("data", {})
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "web_url": data.get("web_url"),
        "draft_url": f"https://app.beehiiv.com/p/{data.get('id')}/edit",
    }


def get_analytics(limit: int = 10) -> list[dict]:
    """Fetch recent post analytics from Beehiiv."""
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
    """Fetch subscriber counts and growth metrics."""
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

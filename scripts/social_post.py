"""
social_post.py — generates social media post drafts after newsletter publish.
Reads the latest local draft for content. Writes three variants:
  1. LinkedIn post (≤150 words, hook-led)
  2. X/Twitter post (≤280 chars)
  3. Community post opener (Reddit/Discord — human edits before posting)

Never auto-posts. Writes drafts to drafts/social_YYYY-MM-DD.md for human review.
Run manually after sending the newsletter.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DRAFTS_DIR = PROJECT_ROOT / "drafts"

CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


def _get_latest_draft() -> tuple[str, Path]:
    """Find the most recent issue draft."""
    drafts = sorted(DRAFTS_DIR.glob("????-??-??_issue_*.md"), reverse=True)
    if not drafts:
        raise FileNotFoundError("No issue drafts found in drafts/ — run curate.py first")
    path = drafts[0]
    return path.read_text(encoding="utf-8"), path


def generate(newsletter_url: str = "") -> dict:
    """
    Generate social post drafts from the latest newsletter draft.

    Args:
        newsletter_url: Published Beehiiv URL (optional — add after publishing)

    Returns:
        dict with linkedin, twitter, community_opener content
    """
    print("[social_post] Generating social media drafts...")

    content, draft_path = _get_latest_draft()

    # Extract free section only (first part before PAYWALL BREAK)
    if "<!-- PAYWALL BREAK -->" in content:
        free_content = content.split("<!-- PAYWALL BREAK -->")[0]
    else:
        free_content = content[:2000]

    url_line = f"\nNewsletter URL (if published): {newsletter_url}" if newsletter_url else ""

    prompt = f"""You write concise, practitioner-focused social media posts for a B2B newsletter about automation and AI tools.
The newsletter serves builders and operators — not beginners, not enterprise.

Here's this week's newsletter free section:
{free_content[:3000]}
{url_line}

Generate three social post variants. Respond with ONLY valid JSON:
{{
  "linkedin": {{
    "text": "LinkedIn post — max 150 words. Lead with the most surprising or counterintuitive signal from this week. No fluff, no 'excited to share'. Hook → insight → brief CTA to subscribe. Use short paragraphs (2-3 sentences max). No emoji unless there's one that genuinely adds meaning.",
    "word_count": [actual word count]
  }},
  "twitter": {{
    "text": "X/Twitter post — max 280 chars including URL. Lead with a specific number or surprising fact from this week. End with a link placeholder [URL] that you'll replace with the real URL.",
    "char_count": [actual char count without URL]
  }},
  "community_opener": {{
    "text": "Community post opener for Reddit/Discord — 100-150 words. Written as a genuine practitioner observation, NOT as newsletter promotion. Frame around a question or observation that invites discussion. The newsletter is mentioned naturally at the end, not forced. This is the version the human will heavily edit before posting.",
    "note": "Human: edit this heavily before posting. Make it sound like you, not a newsletter. The community smells templated posts immediately."
  }}
}}"""

    response = CLIENT.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    result = json.loads(raw)

    # Save to file
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output_path = DRAFTS_DIR / f"social_{date_str}.md"

    output_lines = [
        f"# Social drafts — {date_str}",
        f"*Generated from: {draft_path.name}*",
        "",
        "## LinkedIn",
        "*(max 150 words — edit before posting)*",
        "",
        result["linkedin"]["text"],
        f"\n*Word count: {result['linkedin'].get('word_count', '?')}*",
        "",
        "---",
        "",
        "## X / Twitter",
        "*(max 280 chars — replace [URL] with published URL)*",
        "",
        result["twitter"]["text"],
        f"\n*Char count (without URL): {result['twitter'].get('char_count', '?')}*",
        "",
        "---",
        "",
        "## Community post opener",
        "*(Reddit/Discord — edit heavily before posting, make it sound like you)*",
        "",
        result["community_opener"]["text"],
        "",
        f"---",
        f"*⚠️ {result['community_opener'].get('note', 'Edit before posting')}*",
    ]

    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"[social_post] Drafts saved to: {output_path}")
    print("\n── Social draft preview ──")
    print(f"LinkedIn ({result['linkedin'].get('word_count', '?')} words):")
    print(result["linkedin"]["text"][:200] + "...")
    print(f"\nX ({result['twitter'].get('char_count', '?')} chars):")
    print(result["twitter"]["text"])

    return result


if __name__ == "__main__":
    newsletter_url = sys.argv[1] if len(sys.argv) > 1 else ""
    generate(newsletter_url)

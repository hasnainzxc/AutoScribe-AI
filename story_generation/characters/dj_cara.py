from __future__ import annotations

import os
from typing import Dict, List, Tuple

from config.settings import load_env
from .base import CharacterSpec
from .dj_cara_lines import build_demo_text

try:
    from openai import OpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False


def generate(post: Dict[str, str], *, mode: str = "reddit") -> Tuple[str, Dict]:
    """Generate a single‑speaker DJ Cara monologue (no line prefixes).

    Returns (text, metadata). Text is a continuous monologue suitable for
    single‑track TTS synthesis.
    """
    metadata: Dict[str, object] = {
        "success": False,
        "used_fallback": False,
        "error": None,
        "model_used": None,
        "total_tokens": 0,
        "generation_time": None,
        "character": "DJCARA",
    }

    load_env()
    title = (post.get("title") or "").strip()
    body = (post.get("selftext") or "").strip()

    # Optional tone hint based on subreddit/topic
    subreddit = (post.get("subreddit") or "").lower()
    tone_hint = ""
    if any(k in subreddit for k in ("jokes", "funny", "humor", "comedy")):
        tone_hint = (
            "Lean playful and witty. Include light one‑liners and cheeky asides. "
            "Keep it clean and radio‑friendly.\n"
        )

    style_preamble = (
        "You are DJ Cara (aka DJCARA), an off‑the‑cuff British radio host with a friendly, conversational vibe. "
        "Speak in clear standard English with light modern UK slang when natural (mates, banger, dodgy, wally, proper, knees‑up, innit). "
        "Keep it warm and witty, not shouty; avoid hype/chant or call‑and‑response.\n"
        "Language policy: neutral English with subtle British flavor — never copy sample lines verbatim.\n"
        "Style hints (optional, light touch): 'proper brilliant', 'banger', 'knees‑up', 'hold tight', 'don\'t be a wally'.\n"
        "Delivery: short radio links, complete sentences, clean punctuation for clear TTS phrasing (limited exclamation marks).\n"
        "Target 45–90 seconds spoken (1–3 short paragraphs). Plain text only — no labels, bullets, or markdown."
    )
    if tone_hint:
        style_preamble += "\n" + tone_hint

    prompt = f"""
{style_preamble}

React to this Reddit post with a cohesive, down‑to‑earth monologue that summarizes the key idea and comments on it helpfully:
Title: {title}
Content: {body[:800]}

Constraints:
- Keep it clean and natural; no profanity.
- No line prefixes like 'DJCARA:' — just the monologue.
- Avoid mentioning Reddit explicitly.
- Use only light Caribbean flavor; focus on clarity and usefulness.
"""

    if mode == "demo":
        # Build a curated demo script from original lines
        demo = build_demo_text(max_lines=24)
        metadata["success"] = True
        return demo, metadata

    if not OPENAI_AVAILABLE:
        metadata["used_fallback"] = True
        text = (
            "We inside tonight, who ready fuh vibes? Big chune energy, we leveling de vibes, sweet fuh days! "
            f"{title or 'Real ting trending right now'}, pull up if yuh feel dat — energy, energy, energy! "
            "Limin' together, we mash up de place — run it back one time!"
        )
        return text, metadata

    try:
        import time
        start = time.time()
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are DJ Cara (DJCARA), a British radio host. "
                    "Sound natural and off‑the‑cuff, warm and clear. "
                    "Use light UK slang sparingly; avoid hype‑DJ chanting."
                )},
                {"role": "user", "content": prompt},
            ],
        )
        metadata["generation_time"] = time.time() - start
        metadata["model_used"] = response.model
        if hasattr(response, "usage"):
            metadata["total_tokens"] = response.usage.total_tokens  # type: ignore[attr-defined]

        raw = (response.choices[0].message.content or "").strip()
        # Normalize (strip labels/markdown if any slipped in)
        lines: List[str] = []
        for ln in raw.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s.lower().startswith("djcara:"):
                s = s.split(":", 1)[-1].strip()
            if s and not s[0].isalnum():
                s = s.lstrip("-•* ")
            lines.append(s)
        text = "\n\n".join(lines) if lines else raw
        metadata["success"] = True
        return text, metadata
    except Exception as e:
        metadata["error"] = str(e)
        metadata["used_fallback"] = True
        text = (
            f"Right, here we go. {title or 'A quick one for you today'}. "
            "Let\'s keep it simple and tidy — what it is, why it matters, and what you might do next. Nice and clear."
        )
        return text, metadata


dj_cara_spec = CharacterSpec(
    key="djcara",
    label="djcara",
    single_speaker=True,
    default_voice=os.getenv("TTS_DJCARA_VOICE", "Non_Stop_Pop.mp3"),
    generator=generate,
)

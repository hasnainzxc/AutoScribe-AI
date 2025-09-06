from __future__ import annotations

import os
from typing import Dict, List, Tuple

from config.settings import load_env
from .base import CharacterSpec

try:
    from openai import OpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False


def generate(post: Dict[str, str]) -> Tuple[str, Dict]:
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

    style_preamble = (
        "You are DJ Cara (aka DJCARA), a Trinidadian/Caribbean DJ speaking in a clear, relatable tone. "
        "Write a coherent monologue that explains or reacts to the post in simple, concrete language. "
        "Use light Trini/Caribbean flavor only where it feels natural (e.g., a few words like 'buh', 'dat', 'de', 'meh', 'yuh').\n"
        "Avoid hype fillers, chanty phrasing, or call‑and‑response (no 'energy, energy', 'all hands up', 'pull up', 'we inside').\n"
        "Avoid repeating lines and avoid excessive exclamation points. Keep it calm, friendly, and informative.\n"
        "Target 45–90 seconds spoken.\n"
        "Output 1–3 paragraphs of plain text ONLY. No labels, bullets, or markdown."
    )

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
                {"role": "system", "content": "You are DJ Cara, a Trinidadian hype DJ. Keep it clean, high‑energy, authentic."},
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
            "Aye aye, allyuh ready or what? We inside wid de maddest vibes, level it up! "
            f"{title or 'Sweet fete on de timeline'}, pull up, let we shell de place — energy to de ceiling!"
        )
        return text, metadata


dj_cara_spec = CharacterSpec(
    key="djcara",
    label="djcara",
    single_speaker=True,
    default_voice=os.getenv("TTS_DJCARA_VOICE", "alloy"),
    generator=generate,
)

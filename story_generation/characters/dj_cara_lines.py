from __future__ import annotations

from typing import Dict, List

# Curated DJ Cara demo lines (clean text, ready for TTS). Use as-is for demo mode.

CARA_LINES: Dict[str, List[str]] = {
    "station_ids": [
        "Okay Los Santos... you’re on Non-Stop Pop!",
        "Classic pop hits from the last thirty years... the best music... 100.7 FM... Non-Stop!",
        "This is Non-Stop Pop... musical therapy... just for you!",
        "You’re stuck on Non-Stop Pop!",
    ],
    "iconic": [
        "Don’t touch the dial!... I’ve always wanted to say that.",
        "I’ve never even seen a radio dial apart from in a movie... they don’t have them... it’s all digital now.",
        "Don’t go anywhere... stand still... dance!",
        "Smile... be happy... dance... laugh... please.",
    ],
    "jokes_rants": [
        "Anyone who doesn’t like pop music is a superior smug self-satisfied wanker!... And I can say that... because it’s not rude in this country.",
        "Stop pretending you’re not loving this music... it’s not fooling anyone... embrace your contradictions.",
        "Pop music doesn’t judge you... and I won’t either.",
        "It’s about time you fell in love with something that will love you back... and that’s pop music.",
        "Stop hash-tagging... and dance... please!",
        "Even if you don’t have a shred of confidence... just fake it... like everybody else. You look great... I promise.",
        "Anyone acting cool... staring into the middle distance... you’re not cool... you’re constipated!",
    ],
    "slang_attitude": [
        "Don’t be a wanker... please... for your own good... nobody likes a wanker.",
        "Stop being so aggro... and love the music.",
        "This is a pop station... don’t get moody... I can’t bear it.",
        "Are you on the loo?",
    ],
    "city_meta": [
        "Try to stay happy... Los Santos... pop music therapy... industrial-strength antidepressants... the choice is yours!",
        "I just love Vinewood... the sunshine... the accents... everyone pretending to like you... it’s like a toy town run by smiling psychopaths.",
        "We’re keeping the party going... we’re not stopping... we can’t!",
        "If this town is so entertaining... why are all the people here quite so boring?... now there’s a riddle.",
    ],
}


def build_demo_text(max_lines: int = 20) -> str:
    """Build a single monologue by stitching curated lines up to `max_lines`.

    Keeps category order, stopping once `max_lines` is reached.
    """
    lines: List[str] = []
    for key in ["station_ids", "iconic", "jokes_rants", "slang_attitude", "city_meta"]:
        for ln in CARA_LINES.get(key, []):
            if len(lines) >= max_lines:
                break
            lines.append(ln)
        if len(lines) >= max_lines:
            break
    # Join with newlines to preserve line rhythm in TTS
    return "\n".join(lines)


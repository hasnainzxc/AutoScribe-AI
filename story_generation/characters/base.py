from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple


@dataclass(frozen=True)
class CharacterSpec:
    """Specification describing a character's generation and audio parameters."""

    key: str
    label: str
    single_speaker: bool
    default_voice: str

    # Generator signature returns (text, metadata) for single_speaker characters
    # or (lines, metadata) for multi-speaker characters.
    generator: Callable[[Dict[str, str]], Tuple[object, Dict]]


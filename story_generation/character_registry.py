from __future__ import annotations

from typing import Dict

from .characters.base import CharacterSpec
from .characters import dj_cara_spec, generate_dj_cara


REGISTRY: Dict[str, CharacterSpec] = {
    dj_cara_spec.key: dj_cara_spec,
}

def get_character(key: str) -> CharacterSpec | None:
    return REGISTRY.get((key or "").lower())


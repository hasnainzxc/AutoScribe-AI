"""Subpackage for modules related to story generation.

Provides helper functions and templates for converting raw content into
conversational stories.  In the future, this package can include more
sophisticated narrative constructors, character behaviours, and AI model
wrappers.
"""

"""Expose commonly used functions from the story generation package.

This module makes it convenient to import the dialogue generation helpers without
triggering optional dependencies.  The `create_stories` function depends on
the Reddit ingestion pipeline, which in turn requires the `praw` package.  If
`praw` is not installed, importing `create_stories` will raise an error.  To
avoid unnecessary exceptions when only the dialogue helpers are needed, the
import is done conditionally.
"""

from .dialogue_template import generate_dialogue_from_post, summarise_text  # noqa: F401

# Attempt to import create_stories only if praw is available.  If the import
# fails due to missing dependencies, it will be omitted from __all__.
_available_objects = ["generate_dialogue_from_post", "summarise_text"]
try:
    from .story_generator import create_stories  # type: ignore  # noqa: F401
except Exception:
    create_stories = None  # type: ignore
else:
    _available_objects.append("create_stories")

# Export only successfully imported names
__all__ = _available_objects
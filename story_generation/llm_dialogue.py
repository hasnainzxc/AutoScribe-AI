

from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from config.settings import load_env, get_openrouter_api_key

# Optional dependency: openai client (used with OpenRouter). Fallback if missing.
try:
    import openai  # type: ignore
    from openai import OpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    openai = None  # type: ignore
    OpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format for cleaner output
)
logger = logging.getLogger(__name__)

# Load environment variables centrally
load_env()

# Configure OpenAI client for OpenRouter compatibility if available
api_key = get_openrouter_api_key() or ""
if OPENAI_AVAILABLE:
    openai.api_base = "https://openrouter.ai/api/v1"  # type: ignore[attr-defined]
    if not api_key:
        logger.error("[OpenRouter] No API key found in environment variables!")
    openai.api_key = api_key  # type: ignore[attr-defined]
else:
    logger.warning(
        "[OpenRouter] 'openai' package not installed. Falling back to offline dialogue."
    )

def create_dynamic_dialogue(post: Dict[str, str], num_exchanges: int = 3) -> Tuple[List[str], Dict]:
    """Generate a dynamic dialogue between Rick and Morty about a Reddit post.
    
    Args:
        post: Dictionary containing post information
        num_exchanges: Number of back-and-forth exchanges (default: 3)
        
    Returns:
        Tuple[List[str], Dict]: A tuple containing:
            - List of dialogue lines alternating between Morty and Rick
            - Dictionary with metadata about the generation process
    """
    metadata = {
        "success": False,
        "used_fallback": False,
        "error": None,
        "model_used": None,
        "total_tokens": 0,
        "generation_time": None
    }
    
    logger.info(f"[OpenRouter] Starting dialogue generation for post: {post.get('title', '')[:50]}")
    
    if not post.get('title') or not post.get('selftext'):
        logger.error("[OpenRouter] Invalid post data: missing title or content")
        metadata["error"] = "Invalid post data"
        return _generate_fallback_dialogue(post, metadata)
    
    prompt = f"""Create a dialogue between Rick and Morty discussing this Reddit post:
Title: {post['title']}
Content: {post['selftext']}

The dialogue should:
- Start with Morty asking about the post
- Have Rick explain it in his characteristic style
- Include Rick's burps (*burp*) and catchphrases
- Show Rick's cynical but genius perspective
- Have Morty ask follow-up questions
- Include {num_exchanges} back-and-forth exchanges
- Maintain their personalities (Morty nervous/unsure, Rick confident/dismissive)

Format each line as either 'Morty: [dialogue]' or 'Rick: [dialogue]'"""
    
    logger.info("[OpenRouter] Preparing API call...")

    if not OPENAI_AVAILABLE:
        metadata["error"] = "OpenAI client not installed"
        return _generate_fallback_dialogue(post, metadata)

    try:
        import time
        start_time = time.time()
        
        # Log the prompt being sent
        logger.info("\n" + "="*50)
        logger.info("[OpenRouter] Sending prompt to API:")
        logger.info("-"*50)
        logger.info(f"Reddit Post Title: {post['title']}")
        logger.info(f"Reddit Post Content: {post['selftext'][:200]}...")
        logger.info("-"*50)
        logger.info("Full prompt being sent:")
        logger.info(prompt)
        logger.info("="*50 + "\n")
        
        # Call OpenRouter API
        logger.info("[OpenRouter] Making API request...")
        
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )

            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a writer for Rick and Morty, crafting dialogues that perfectly capture their personalities and speech patterns."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Get the raw dialogue text
            raw_dialogue = response.choices[0].message.content

            logger.info("\n" + "="*50)
            logger.info("[OpenRouter] API Response Received:")
            logger.info("-"*50)
            logger.info(raw_dialogue)
            logger.info("="*50 + "\n")

            # Process the dialogue into proper format
            dialogue_lines = []
            for line in raw_dialogue.split('\n'):
                line = line.strip()
                if line and (line.startswith('Rick:') or line.startswith('Morty:')):
                    dialogue_lines.append(line)

            logger.info(f"\n[OpenRouter] Successfully processed {len(dialogue_lines)} dialogue lines")
            logger.info("\nProcessed dialogue lines:")
            for i, line in enumerate(dialogue_lines, 1):
                logger.info(f"{i}. {line}")

        except Exception as api_error:
            logger.error(f"\n[OpenRouter] API Call Failed: {str(api_error)}\n")
            raise
        
        generation_time = time.time() - start_time
        logger.info(f"[OpenRouter] Received response in {generation_time:.2f} seconds")
        
        # Log the response
        logger.info("\n" + "="*50)
        logger.info("[OpenRouter] Received response:")
        logger.info("-"*50)
        logger.info("Generated dialogue:")
        logger.info(response.choices[0].message.content)
        logger.info("-"*50)
        logger.info(f"Model used: {response.model}")
        if hasattr(response, 'usage'):
            logger.info(f"Token usage: {response.usage.total_tokens} tokens")
        logger.info("="*50 + "\n")
        
        # Update metadata
        metadata.update({
            "success": True,
            "model_used": response.model,
            "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0,
            "generation_time": generation_time
        })
        
        # Extract and process the dialogue
        dialogue_text = response.choices[0].message.content
        dialogue_lines = [line.strip() for line in dialogue_text.split('\n') if line.strip()]
        
        # Filter for only lines that start with "Rick:" or "Morty:"
        dialogue = [
            line for line in dialogue_lines 
            if line.startswith("Rick:") or line.startswith("Morty:")
        ]
        
        if not dialogue:
            logger.warning("[OpenRouter] No valid dialogue lines found in response")
            return _generate_fallback_dialogue(post, metadata)
            
        logger.info(f"[OpenRouter] Successfully generated {len(dialogue)} lines of dialogue")
        return dialogue, metadata

    except Exception as e:
        logger.error(f"[OpenRouter] Unexpected error: {str(e)}")
        metadata["error"] = f"Unexpected error: {str(e)}"
        return _generate_fallback_dialogue(post, metadata)

def _generate_fallback_dialogue(post: Dict[str, str], metadata: Dict) -> Tuple[List[str], Dict]:
    """Generate a fallback dialogue when the API call fails."""
    logger.warning("\n" + "="*50)
    logger.warning("[OpenRouter] API CALL FAILED - Using fallback dialogue generation")
    logger.warning(f"Error: {metadata.get('error', 'Unknown error')}")
    logger.warning("="*50 + "\n")
    
    metadata["used_fallback"] = True
    fallback_dialogue = [
        f"Morty: Ah geez Rick, I was reading about '{post['title']}' on Reddit. W-what's that all about?",
        f"Rick: Listen Morty, {post['selftext'][:200]}... *burp* And that's the way the news goes!"
    ]
    
    logger.warning("[OpenRouter] Fallback dialogue generated:")
    logger.warning("-"*50)
    for line in fallback_dialogue:
        logger.warning(line)
    logger.warning("-"*50 + "\n")
    
    return fallback_dialogue, metadata

def log_generation_stats(metadata: Dict) -> None:
    """Log statistics about the dialogue generation."""
    status = "✓" if metadata["success"] else "✗"
    logger.info("=" * 50)
    logger.info(f"Generation Status: {status}")
    logger.info(f"Used Fallback: {metadata['used_fallback']}")
    if metadata["error"]:
        logger.info(f"Error: {metadata['error']}")
    if metadata["model_used"]:
        logger.info(f"Model: {metadata['model_used']}")
    if metadata["total_tokens"]:
        logger.info(f"Tokens Used: {metadata['total_tokens']}")
    if metadata["generation_time"]:
        logger.info(f"Generation Time: {metadata['generation_time']:.2f}s")


def create_djcara_dialogue(post: Dict[str, str], bars: int = 16) -> Tuple[List[str], Dict]:
    """Generate a DJ Cara (Trinidadian/Caribbean) hype script for a single continuous track.

    Returns (lines, metadata). Lines are still prefixed with 'DJCARA:' but are
    intended to be joined into one spoken monologue for TTS.
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
    if not title:
        metadata["error"] = "Missing post title"
    
    style_preamble = (
        "You are DJ Cara (aka DJCARA), a Trinidadian/Caribbean club DJ and hype MC. "
        "Deliver a continuous spoken hype story (like hosting over a beat). "
        "Use Trini/Caribbean cadence with orthography cues (ah, buh, dat, de, doh, meh, yuh).\n"
        "Keep unstressed words quick, stretch stressed syllables on drops. Use repetition for emphasis ('Energy, energy, energy!').\n"
        "Work in authentic party slang when natural: fete, limin', vibes, mash up, wine/whine, riddim, big chune, pull up, shell d place, level de vibes, run it back, mad ting, real ting, sweet fuh days.\n"
        "Do call-and-response prompts: 'who ready', 'we inside', 'all hands up'. Keep it friendly and high energy.\n"
        "Target length: 45–90 seconds when spoken; adapt to the post's vibe (shorter if light, longer if rich).\n"
        "Output one idea per line (lines will be joined for a single TTS track). Prefix each line with 'DJCARA: '. Avoid profanity."
    )

    prompt = f"""
{style_preamble}

React to this Reddit post with hype lines that fit the vibe:
Title: {title}
Content: {body[:800]}

Instructions:
- 10–24 lines total. Each line <= 120 chars.
- Make it continuous, cohesive (not disjoint bullets); vary commands and hype.
- Keep it natural Trini cadence with spellings like 'de', 'yuh', 'doh'.
- Reference the post's vibe/theme without naming Reddit explicitly.
- No stage directions, only spoken lines.
- Strictly prefix each line with 'DJCARA: '.
"""

    if not OPENAI_AVAILABLE:
        metadata["used_fallback"] = True
        lines = [
            "DJCARA: we inside tonight, who ready fuh vibes?",
            f"DJCARA: big chune vibes — {title or 'real ting trending'}, level de vibes!",
            "DJCARA: pull up if yuh feel dat, energy energy energy!",
            "DJCARA: leh we shell d place, run it back one time!",
        ]
        return lines, metadata

    try:
        import time
        start = time.time()
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are DJ Cara, a Trinidadian hype DJ. Keep it clean, high-energy, authentic."},
                {"role": "user", "content": prompt},
            ],
        )
        metadata["generation_time"] = time.time() - start
        metadata["model_used"] = response.model
        if hasattr(response, "usage"):
            metadata["total_tokens"] = response.usage.total_tokens  # type: ignore[attr-defined]

        raw = response.choices[0].message.content or ""
        lines: List[str] = []
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                continue
            if not s.lower().startswith("djcara:"):
                continue
            lines.append(s)
        if not lines:
            raise ValueError("No DJCARA lines parsed")
        metadata["success"] = True
        return lines, metadata
    except Exception as e:
        metadata["error"] = str(e)
        metadata["used_fallback"] = True
        fallback = [
            "DJCARA: a a — allyuh ready or what?",
            f"DJCARA: de vibes set — {title or 'sweet fete'} — level de vibes!",
            "DJCARA: big chune loading, pull up if yuh feel dat!",
            "DJCARA: mad ting, we shell d place — run it back one time!",
        ]
        return fallback, metadata
    logger.info("=" * 50)

if __name__ == "__main__":
    # Example usage
    test_post = {
        "title": "How to make easy money online",
        "selftext": "Found a great way to earn $50/day by testing websites. All you need is a computer and internet connection.",
        "url": "https://reddit.com/r/beermoney/test"
    }
    
    dialogue, metadata = create_dynamic_dialogue(test_post)
    log_generation_stats(metadata)
    for line in dialogue:
        print(line)



from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import openai
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format for cleaner output
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure OpenAI client for OpenRouter compatibility
openai.api_base = "https://openrouter.ai/api/v1"
api_key = os.getenv("OPENROUTER_API_KEY", "")
if not api_key:
    logger.error("[OpenRouter] No API key found in environment variables!")
openai.api_key = api_key

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
                api_key=os.getenv("OPENROUTER_API_KEY"),
                headers={"HTTP-Referer": "https://github.com/yourusername/content_pipeline"}
            )
            
            response = client.chat.completions.create(
                model="anthropic/claude-2",
                messages=[
                    {"role": "system", "content": "You are a writer for Rick and Morty, crafting dialogues that perfectly capture their personalities and speech patterns."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            logger.info("\n" + "="*50)
            logger.info("[OpenRouter] API Response Received:")
            logger.info("-"*50)
            logger.info(response.choices[0].message.content)
            logger.info("="*50 + "\n")
            
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

    except openai.error.AuthenticationError as e:
        logger.error(f"[OpenRouter] Authentication failed: {str(e)}")
        metadata["error"] = "Authentication failed"
        return _generate_fallback_dialogue(post, metadata)
    except openai.error.APIError as e:
        logger.error(f"[OpenRouter] API error: {str(e)}")
        metadata["error"] = f"API error: {str(e)}"
        return _generate_fallback_dialogue(post, metadata)
    except openai.error.RateLimitError as e:
        logger.error(f"[OpenRouter] Rate limit exceeded: {str(e)}")
        metadata["error"] = "Rate limit exceeded"
        return _generate_fallback_dialogue(post, metadata)
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

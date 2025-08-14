"""LLM integration module for generating dynamic Rick and Morty dialogues.

This module uses OpenRouter's API to generate more interactive and dynamic
conversations between Rick and Morty based on Reddit posts. It maintains their
characteristic speech patterns and personalities while creating engaging dialogues.
"""

from __future__ import annotations

import os
from typing import List, Dict
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure OpenAI client for OpenRouter compatibility
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = os.getenv("OPENROUTER_API_KEY", "")

def create_dynamic_dialogue(post: Dict[str, str], num_exchanges: int = 3) -> List[str]:
    """Generate a dynamic dialogue between Rick and Morty about a Reddit post.
    
    Args:
        post: Dictionary containing post information
        num_exchanges: Number of back-and-forth exchanges (default: 3)
        
    Returns:
        List of dialogue lines alternating between Morty and Rick
    """
    # Create the prompt for the LLM
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

    try:
        # Call OpenRouter API
        response = openai.ChatCompletion.create(
            model="anthropic/claude-2",  # or other available models
            messages=[
                {"role": "system", "content": "You are a writer for Rick and Morty, crafting dialogues that perfectly capture their personalities and speech patterns."},
                {"role": "user", "content": prompt}
            ],
            headers={"HTTP-Referer": "https://github.com/yourusername/content_pipeline"},  # Replace with your repo
        )
        
        # Extract and process the dialogue
        dialogue_text = response.choices[0].message.content
        dialogue_lines = [line.strip() for line in dialogue_text.split('\n') if line.strip()]
        
        # Filter for only lines that start with "Rick:" or "Morty:"
        dialogue = [
            line for line in dialogue_lines 
            if line.startswith("Rick:") or line.startswith("Morty:")
        ]
        
        return dialogue

    except Exception as e:
        # Fallback to basic dialogue if API call fails
        return [
            f"Morty: Ah geez Rick, I was reading about '{post['title']}' on Reddit. W-what's that all about?",
            f"Rick: Listen Morty, {post['selftext'][:200]}... *burp* And that's the way the news goes!"
        ]

if __name__ == "__main__":
    # Example usage
    test_post = {
        "title": "How to make easy money online",
        "selftext": "Found a great way to earn $50/day by testing websites. All you need is a computer and internet connection.",
        "url": "https://reddit.com/r/beermoney/test"
    }
    
    dialogue = create_dynamic_dialogue(test_post)
    for line in dialogue:
        print(line)

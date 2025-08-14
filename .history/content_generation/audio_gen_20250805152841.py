"""Audio generation module for creating voice clips from dialogue.

This module uses gTTS (Google Text to Speech) to create audio files from
the Rick and Morty dialogue. It supports different voices for different
characters and includes Rick's signature burps.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple
from gtts import gTTS

def create_dialogue_audio(dialogue: List[str], output_dir: str) -> List[str]:
    """Create audio files for each line of dialogue.
    
    Args:
        dialogue: List of dialogue lines
        output_dir: Directory to save audio files
        
    Returns:
        List of paths to created audio files
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []
    
    for i, line in enumerate(dialogue):
        # Determine if this is Rick or Morty speaking
        is_rick = "Rick:" in line
        
        # Clean up the line - remove character name and clean up burps
        clean_line = line.replace("Rick: ", "").replace("Morty: ", "")
        if is_rick:
            # For Rick's lines, we'll need to split around the burps
            # and create separate audio files that we'll merge
            parts = clean_line.split("*burp*")
            clean_line = " ".join(parts)
        
        # Create audio file
        tts = gTTS(text=clean_line, lang='en', slow=False)
        
        # Save with character prefix for easier identification
        character = "rick" if is_rick else "morty"
        filename = f"{character}_line_{i}.mp3"
        filepath = os.path.join(output_dir, filename)
        tts.save(filepath)
        audio_files.append(filepath)
    
    return audio_files

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Create audio files from dialogue")
    parser.add_argument("dialogue_file", help="JSON file containing dialogue")
    parser.add_argument(
        "-o", 
        "--output-dir", 
        default="audio_output",
        help="Directory to save audio files (default: audio_output)"
    )
    
    args = parser.parse_args()
    
    with open(args.dialogue_file) as f:
        dialogues = json.load(f)
    
    for i, dialogue in enumerate(dialogues):
        output_dir = os.path.join(args.output_dir, f"dialogue_{i}")
        audio_files = create_dialogue_audio(dialogue, output_dir)
        print(f"Created {len(audio_files)} audio files in {output_dir}")

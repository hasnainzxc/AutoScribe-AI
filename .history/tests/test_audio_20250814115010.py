"""Test script for audio generation."""

from content_generation.audio_gen import create_dialogue_audio
import os

def test_audio_generation():
    """Test the audio generation with sample dialogue."""
    test_dialogue = [
        "Rick: Listen up Morty *burp* I've got something important to tell you!",
        "Morty: Oh geez Rick, w-what is it this time?",
        "Rick: We're gonna make some money Morty! *burp* Quick and easy money!",
        "Morty: I don't know Rick, your schemes usually end up pretty dangerous..."
    ]
    
    print("\nTesting audio generation...")
    print("-" * 50)
    print("Input dialogue:")
    for line in test_dialogue:
        print(line)
    print("-" * 50)
    
    # Create test output directory
    test_output = "test_output/audio"
    os.makedirs(test_output, exist_ok=True)
    
    audio_files = create_dialogue_audio(test_dialogue, test_output)
    
    print("\nGenerated audio files:")
    print("-" * 50)
    for file in audio_files:
        print(f"Created: {file}")
    
    return audio_files

if __name__ == "__main__":
    test_audio_generation()

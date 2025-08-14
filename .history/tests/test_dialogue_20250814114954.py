"""Test script for dialogue generation."""

from story_generation.llm_dialogue import create_dynamic_dialogue

def test_dialogue_generation():
    """Test the dialogue generation with a sample post."""
    test_post = {
        "title": "Quick way to earn $50",
        "selftext": "Found a great method to earn money online by testing websites. All you need is a computer and internet connection. Payment is sent via PayPal within 24 hours.",
        "url": "https://reddit.com/r/test"
    }

    print("\nTesting dialogue generation...")
    print("-" * 50)
    print(f"Input post: {test_post['title']}")
    print("-" * 50)
    
    dialogue, metadata = create_dynamic_dialogue(test_post)
    
    print("\nGenerated dialogue:")
    print("-" * 50)
    for line in dialogue:
        print(line)
    
    print("\nGeneration metadata:")
    print("-" * 50)
    for key, value in metadata.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_dialogue_generation()

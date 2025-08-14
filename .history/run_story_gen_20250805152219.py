import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath('..'))

from content_pipeline.story_generation.story_generator import create_stories

if __name__ == "__main__":
    dialogues = create_stories('beermoney', 3)
    print(dialogues)

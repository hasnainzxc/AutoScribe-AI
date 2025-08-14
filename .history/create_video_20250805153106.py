"""Main script to generate a complete video from Reddit posts.

This script combines all the components of the pipeline:
1. Fetches posts from Reddit
2. Generates Rick and Morty dialogue
3. Creates audio for the dialogue
4. Generates a video with the audio
"""

import os
import json
from pathlib import Path

from story_generation.story_generator import create_stories
from content_generation.audio_gen import create_dialogue_audio
from content_generation.video_gen import create_video_from_audio

def create_full_video(
    subreddit: str = "beermoney",
    num_posts: int = 3,
    sort: str = "top",
    time_filter: str = "week",
    output_dir: str = "output",
) -> str:
    """Create a complete video from Reddit posts.
    
    Args:
        subreddit: Subreddit to pull posts from
        num_posts: Number of posts to process
        sort: How to sort posts
        time_filter: Time filter for top posts
        output_dir: Directory for output files
        
    Returns:
        Path to the final video file
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Generate stories
    print("Generating stories...")
    dialogues = create_stories(
        subreddit=subreddit,
        number_of_posts=num_posts,
        sort=sort,
        time_filter=time_filter,
    )
    
    # Save dialogues for reference
    dialogue_file = os.path.join(output_dir, "dialogues.json")
    with open(dialogue_file, "w") as f:
        json.dump(dialogues, f, indent=2)
    
    # 2. Generate audio for each dialogue
    print("Generating audio...")
    all_audio_files = []
    for i, dialogue in enumerate(dialogues):
        dialogue_dir = os.path.join(output_dir, f"dialogue_{i}")
        audio_files = create_dialogue_audio(dialogue, dialogue_dir)
        all_audio_files.extend(audio_files)
    
    # 3. Create the video
    print("Generating video...")
    video_path = os.path.join(output_dir, "final_video.mp4")
    video_path = create_video_from_audio(
        all_audio_files,
        video_path,
    )
    
    print(f"Video creation complete! Output at: {video_path}")
    return video_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a Rick and Morty style video from Reddit posts"
    )
    parser.add_argument(
        "subreddit",
        help="The subreddit to pull posts from"
    )
    parser.add_argument(
        "-n",
        "--num-posts",
        type=int,
        default=3,
        help="Number of posts to process (default: 3)"
    )
    parser.add_argument(
        "-s",
        "--sort",
        choices=["hot", "new", "rising", "top"],
        default="top",
        help="Sort method for posts (default: top)"
    )
    parser.add_argument(
        "-t",
        "--time-filter",
        choices=["all", "year", "month", "week", "day", "hour"],
        default="week",
        help="Time filter for top posts (default: week)"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )
    
    args = parser.parse_args()
    video_path = create_full_video(
        subreddit=args.subreddit,
        num_posts=args.num_posts,
        sort=args.sort,
        time_filter=args.time_filter,
        output_dir=args.output_dir,
    )

"""Video generation module for creating animated content from audio and images.

This module takes the audio files created by audio_gen.py and combines them
with background images and simple animations to create a video in the style
of a simple animated conversation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

def create_video_from_audio(
    audio_files: List[str],
    output_path: str,
    background_image: str = None,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Create a video from a list of audio files.
    
    Args:
        audio_files: List of paths to audio files
        output_path: Where to save the final video
        background_image: Optional path to background image
        width: Video width in pixels
        height: Video height in pixels
        
    Returns:
        Path to the created video file
    """
    clips = []
    
    # If no background image provided, create a simple gradient
    if not background_image:
        # Create a simple gradient background
        array = np.zeros((height, width, 3))
        for i in range(height):
            array[i, :] = [i/height*255]*3
        background = Image.fromarray(array.astype('uint8'))
        background.save("temp_background.png")
        background_image = "temp_background.png"
    
    for audio_file in audio_files:
        # Load the audio
        audio = AudioFileClip(audio_file)
        
        # Create a video clip from the background image
        video = ImageClip(background_image)
        
        # Set the audio
        video = video.set_audio(audio)
        
        # Set the duration to match the audio
        video = video.set_duration(audio.duration)
        
        clips.append(video)
    
    # Concatenate all clips
    final_clip = concatenate_videoclips(clips)
    
    # Write the result
    final_clip.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac'
    )
    
    # Clean up
    if not background_image:
        os.remove("temp_background.png")
    
    return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create video from audio files")
    parser.add_argument(
        "audio_dir",
        help="Directory containing audio files"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.mp4",
        help="Output video file (default: output.mp4)"
    )
    parser.add_argument(
        "-b",
        "--background",
        help="Background image to use"
    )
    
    args = parser.parse_args()
    
    # Get all audio files in the directory
    audio_files = sorted([
        os.path.join(args.audio_dir, f)
        for f in os.listdir(args.audio_dir)
        if f.endswith('.mp3')
    ])
    
    video_path = create_video_from_audio(
        audio_files,
        args.output,
        args.background
    )
    print(f"Created video: {video_path}")

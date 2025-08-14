"""Test script for video generation."""

from content_generation.video_gen import create_video_from_audio
import os

def test_video_generation():
    """Test the video generation with sample audio files."""
    # First, ensure we have some audio files to test with
    from test_audio import test_audio_generation
    
    print("\nTesting video generation...")
    print("-" * 50)
    
    # Get audio files from audio test
    audio_files = test_audio_generation()
    
    # Create test output directory
    test_output = "test_output/video"
    os.makedirs(test_output, exist_ok=True)
    
    # Generate video
    output_path = os.path.join(test_output, "test_video.mp4")
    video_path = create_video_from_audio(audio_files, output_path)
    
    print("\nVideo generation results:")
    print("-" * 50)
    print(f"Created video: {video_path}")
    print(f"Video size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    print(f"Location: {os.path.abspath(video_path)}")

if __name__ == "__main__":
    test_video_generation()

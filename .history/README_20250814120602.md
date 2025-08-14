# AutoScribe-AI 🤖

A Python-based content automation pipeline that transforms social media posts into engaging character dialogues and videos. This AI-powered system automatically generates dynamic conversations, converts them into dialogue videos with text-to-speech, and creates compelling short-form content.

## Features

- 🤖 AI-powered dialogue generation using OpenRouter/OpenAI
- 🎭 Character-accurate Rick and Morty dialogue style with burps and catchphrases
- 🎤 Text-to-speech audio generation using Google TTS
- 🎬 Automated video creation with MoviePy
- 📱 Flexible Reddit post fetching (top/hot/new, time filters)
- 📊 Detailed logging and error tracking
- ⚡ Fast and efficient video processing

## Directory Structure

```

## Running Instructions

### Complete Pipeline

Generate videos from Reddit posts using the main script:
```bash
python create_video.py [subreddit] -n [number_of_posts] -s [sort] -t [time_filter]
```

Example:
```bash
python create_video.py beermoney -n 2 -s top -t week
```

Arguments:
- `subreddit`: Name of the subreddit to pull posts from
- `-n, --number`: Number of posts to process (default: 3)
- `-s, --sort`: How to sort posts ('hot', 'new', 'rising', 'top') (default: 'top')
- `-t, --time`: Time filter for 'top' sorting ('hour', 'day', 'week', 'month', 'year', 'all') (default: 'week')

### Individual Components

You can also run each component separately for testing or development:

#### 1. Reddit Post Fetching
```bash
# Test Reddit post fetching
python -c "from ingestion.reddit_ingest import fetch_subreddit_posts; posts = fetch_subreddit_posts('beermoney', limit=2); print(posts)"
```

#### 2. Story Generation
```bash
# Generate dialogue from a specific post
python story_generation/story_generator.py
```

Example test script for dialogue generation (`test_dialogue.py`):
```python
from story_generation.llm_dialogue import create_dynamic_dialogue

test_post = {
    "title": "Quick way to earn $50",
    "selftext": "Found a great method to earn money online...",
    "url": "https://reddit.com/r/test"
}

dialogue, metadata = create_dynamic_dialogue(test_post)
for line in dialogue:
    print(line)
```

#### 3. Audio Generation
```bash
# Test audio generation with sample text
python content_generation/audio_gen.py
```

Example test script for audio (`test_audio.py`):
```python
from content_generation.audio_gen import create_dialogue_audio

test_dialogue = [
    "Rick: Let me tell you something Morty *burp*",
    "Morty: Oh geez, Rick, I don't know about this"
]

audio_files = create_dialogue_audio(test_dialogue, "test_output")
print(f"Created audio files: {audio_files}")
```

#### 4. Video Generation
```bash
# Test video generation with sample audio
python content_generation/video_gen.py
```

Example test script for video (`test_video.py`):
```python
from content_generation.video_gen import create_video_from_audio

audio_files = ["dialogue1.mp3", "dialogue2.mp3"]
video_path = create_video_from_audio(audio_files, "test_output/final.mp4")
print(f"Created video: {video_path}")
```

### Development Testing

For development and testing, you can use these commands:

1. Test Reddit API connection:
```bash
python -c "from ingestion.reddit_ingest import test_reddit_connection; test_reddit_connection()"
```

2. Test OpenRouter/OpenAI API:
```bash
python -c "from story_generation.llm_dialogue import test_api_connection; test_api_connection()"
```

3. Test audio generation:
```bash
python -c "from content_generation.audio_gen import test_audio; test_audio()"
```

4. Test complete pipeline with debug logging:
```bash
python create_video.py beermoney -n 1 -s top -t week --debug
```

### Output Locations

- Audio files: `output/dialogue/`
- Final videos: `output/`
- Logs: `output/logs/`
- Temporary files: `output/temp/`

## How It Works

1. **Reddit Post Fetching**:
   - Uses PRAW to fetch posts from specified subreddit
   - Supports various sorting methods and time filters
   - Handles post filtering and content extraction

2. **AI Dialogue Generation**:
   - Connects to OpenRouter/OpenAI API
   - Generates character-accurate Rick and Morty dialogues
   - Maintains personalities and speech patterns
   - Includes Rick's signature burps and catchphrases

3. **Audio Generation**:
   - Converts dialogue to speech using Google TTS
   - Processes character-specific speech patterns
   - Handles special effects and timing

4. **Video Creation**:
   - Combines audio with visual elements using MoviePy
   - Creates seamless transitions between scenes
   - Generates final MP4 output

## Directory Structure

```
content_pipeline/
├── ingestion/               # Reddit data ingestion
│   ├── __init__.py
│   └── reddit_ingest.py    # Reddit API interaction
├── story_generation/        # AI dialogue creation
│   ├── __init__.py
│   ├── dialogue_template.py # Dialogue templates
│   ├── llm_dialogue.py     # AI dialogue generation
│   └── story_generator.py  # Story orchestration
├── content_generation/      # Audio/video creation
│   ├── __init__.py
│   ├── audio_gen.py        # Text-to-speech
│   └── video_gen.py        # Video assembly
├── .env                    # API credentials
├── requirements.txt        # Python dependencies
└── create_video.py        # Main script
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- 🐛 Report bugs and issues
- ✨ Propose new features
- 🛠️ Submit pull requests
- 📝 Improve documentation
- 🎨 Enhance video generation

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**:
   ```
   ModuleNotFoundError: No module named 'xxx'
   ```
   Solution: Make sure you've installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Authentication Errors**:
   ```
   Authentication failed for API xxx
   ```
   Solution: Check your `.env` file has the correct API keys.

3. **Video Generation Errors**:
   ```
   MoviePy Error: FFMPEG not found
   ```
   Solution: Install FFmpeg and ensure it's in your system PATH.

### Getting Help

If you encounter any issues:
1. Check the error logs (the script provides detailed logging)
2. Verify your API credentials
3. Ensure all dependencies are installed correctly
4. Open an issue on GitHub with the error details

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI/OpenRouter for AI dialogue generation
- Reddit API for content access
- Google Text-to-Speech for voice generation
- MoviePy for video creation
- The Rick and Morty community for inspiration

## Prerequisites

- Python 3.12 or higher
- Reddit API credentials (from https://www.reddit.com/prefs/apps)
- OpenRouter API key (from https://openrouter.ai/)
- FFmpeg (required by moviepy for video processing)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd content_pipeline
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables in `.env`:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ContentPipeline/0.1.0
OPENROUTER_API_KEY=your_openrouter_api_key
```
pip install -e .
```

This will install all required dependencies:
- `praw`: Reddit API wrapper
- `python-dotenv`: Environment variable management
- `gTTS`: Google Text-to-Speech
- `moviepy`: Video creation and editing
- `numpy`: Required for video processing
- `Pillow`: Image processing

## Configuration

1. Create a `.env` file in the project root with your Reddit API credentials:
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ContentPipeline/0.1.0
```

To get Reddit API credentials:
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Choose "script"
4. Fill in any name and description
5. For "redirect uri" put http://localhost:8080
6. Click create app
7. Use the client ID and secret in your .env file

## Usage

### Basic Usage

Generate a video from top posts in r/beermoney:
```bash
python create_video.py beermoney -n 3 -s top -t week
```

### Command Line Arguments

- `subreddit`: Name of the subreddit to pull posts from
- `-n, --num-posts`: Number of posts to process (default: 3)
- `-s, --sort`: Sort method ['hot', 'new', 'rising', 'top'] (default: 'top')
- `-t, --time-filter`: Time filter for top posts ['all', 'year', 'month', 'week', 'day', 'hour'] (default: 'week')
- `-o, --output-dir`: Output directory (default: 'output')

### Output Structure

The script creates:
- `output/dialogues.json`: Generated dialogue scripts
- `output/dialogue_X/`: Audio files for each dialogue
- `output/final_video.mp4`: The final compiled video

## How It Works

1. **Data Ingestion** (`reddit_ingest.py`):
   - Connects to Reddit using PRAW
   - Fetches posts based on specified criteria
   - Filters and cleans post content

2. **Story Generation** (`story_generator.py`, `dialogue_template.py`):
   - Transforms Reddit posts into dialogue format
   - Adds Rick and Morty's characteristic speech patterns
   - Structures conversations naturally

3. **Content Generation** (`audio_gen.py`, `video_gen.py`):
   - Converts dialogue to speech using Google TTS
   - Generates audio files for each line
   - Creates video with background and audio

## Future Improvements

- Add custom character voices using voice cloning
- Implement better text-to-speech with emotional inflections
- Add animations and visual effects
- Improve dialogue generation with AI
- Add support for more content sources
- Implement custom background images or animations
- Add more character interactions and complexity
- Support for multiple languages
- Add background music and sound effects

## Contributing

Feel free to:
- Submit bug reports
- Propose new features
- Add better dialogue templates
- Improve video generation
- Enhance audio quality
- Add new content sources


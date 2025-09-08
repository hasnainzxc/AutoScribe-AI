# AutoScribe-AI (Audio‑Only)

Generate Rick & Morty‑style (and DJ Cara‑style) dialogues from Reddit posts and render each line to audio files. Chatterbox (port 8014) is the supported TTS server; the pipeline falls back to Google gTTS when not configured.

---

## Highlights

* Dialogue generation via OpenRouter/OpenAI
* Rick & Morty‑style prompt templates
* Google gTTS (default) or OpenAI‑compatible TTS backend
* Reddit ingestion with sort and time filters
* Chatterbox TTS support (port 8014)

---

## Project Structure

```
AutoScribe-AI/
├── content_generation/        # Audio creation
│   └── audio_gen.py           # gTTS or server‑based TTS
├── ingestion/
│   └── reddit_ingest.py       # Reddit API (PRAW)
├── story_generation/
│   ├── dialogue_template.py
│   ├── llm_dialogue.py
│   └── story_generator.py
├── run_story_gen.py           # End‑to‑end audio pipeline
├── requirements.txt
├── README.md                  # This file
└── .env                       # API credentials (not committed)
```

> Note: This repo focuses on audio generation. For high‑quality voices, run a
> Chatterbox TTS server locally on port 8014 and set the environment variables
> from `.env.example`. Google gTTS remains as a safe fallback.

---

## Quick Start

### 1) Install (root env)

```bash
python -m venv .venv
source .venv/bin/activate 

source /home/hairzee/.venvs/autoscribe-ai/bin/activate
  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2) Configure creds (`.env` at repo root)

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ContentPipeline/0.1.0
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3) Run full pipeline

```bash
# Default (Rick & Morty)
python run_story_gen.py beermoney -n 2 -s top -t week -o output

# DJ Cara (single-track) using default Non_Stop_Pop voice
# (Set CHATTERBOX_BASE_URL=http://localhost:8014 first.)
python run_story_gen.py beermoney -c djcara -s top -t week -o audio

# DJ Cara with an explicit voice (exact filename from /get_predefined_voices)
python run_story_gen.py beermoney -c djcara -s top -t week -o audio --tts-voice "Non_Stop_Pop.mp3"

# List available voices from Chatterbox
python run_story_gen.py --list-voices

# Shortcut: Explicitly use the Non_Stop_Pop voice
python run_story_gen.py beermoney -c djcara -s top -t week -o audio --cara

# Optional: pass TTS tuning parameters
# (temperature, exaggeration, cfg guidance, speed)
python run_story_gen.py beermoney -c djcara -s top -t week -o audio \
  --tts-temp 0.6 --tts-exag 0.9 --tts-cfg 0.3 --tts-speed 1.0

```

Outputs:

* `output/dialogues.json` — saved text + metadata
* `output/*.mp3` — combined audio files (per character or single‑track)

---

## TTS Backends

### Chatterbox TTS (port 8014)

Run a local Chatterbox TTS server on port 8014. Minimal env:

```
CHATTERBOX_BASE_URL=http://localhost:8014
CHATTERBOX_API_KEY=your_tts_server_key
TTS_MODEL=gpt-4o-mini-tts
TTS_DEFAULT_VOICE=alloy
TTS_DJCARA_VOICE=Non_Stop_Pop.mp3
TTS_RESPONSE_FORMAT=mp3
```

Tips
- List available voices: GET `http://localhost:8014/get_predefined_voices` (returns `display_name` and `filename`).
- Outputs listing: GET `http://localhost:8014/api/outputs?limit=100` (optionally `&prefix=` to filter by filename prefix).
- The pipeline’s Chatterbox client logs each request (endpoints, voice, text length) and downloads the newest output to your chosen `-o/--output` directory.

The pipeline automatically falls back to Google gTTS if a server isn’t configured or fails at runtime.

#### Cara Pacing Defaults

DJ Cara now uses clarity‑first pacing by default to avoid “eating words” while keeping the Trini flavor:

- Default speed factor: 0.88 (slightly slower than 1.0)
- Slightly reduced exaggeration for cleaner enunciation
- Optional smaller chunk size if your server benefits from it

You can override via environment variables:

```
# DJ Cara-specific overrides
TTS_DJCARA_SPEED_FACTOR=0.88   # or TTS_DJCARA_SPEED
TTS_DJCARA_EXAG=0.85
# Optionally let the server work smaller chunks for better phrasing
# TTS_DJCARA_CHUNK_SIZE=100
```

CLI flags like `--tts-speed` and `--tts-exag` still work and override these defaults for a run.

### Google TTS (default in examples)

Works out of the box via `gTTS` in `content_generation/audio_gen.py`.

---

## Intro/Outro (Optional)

Place your stingers in `./intro` and `./outro` as audio files (MP3 preferred; WAV also supported when `pydub` is installed). After synthesis, the CLI can prompt to auto‑prepend/append them to the generated track(s).

Usage:

```
# Interactive prompt at the end (default)
python run_story_gen.py beermoney -c djcara -o audio

# Force adding intro/outro without a prompt
python run_story_gen.py beermoney -c djcara -o audio --with-intro-outro

# Force no intro/outro
python run_story_gen.py beermoney -c djcara -o audio --without-intro-outro
```

Outputs are written alongside originals with the suffix `_with_intro_outro.mp3`.

Notes:
- With `pydub` available, most common formats are supported and exported to MP3.
- Without `pydub`, all files must be MP3 and the tool will use ffmpeg concat.

---

## Commands and Tests

### Ingestion

```bash
python -c "from ingestion.reddit_ingest import fetch_subreddit_posts; print(fetch_subreddit_posts('beermoney', limit=2))"
```

### Story generation

```bash
python story_generation/story_generator.py
```

### Audio (gTTS demo)

```bash
python content_generation/audio_gen.py
```

<!-- Video creation code was removed in the audio‑only refactor. -->

---

## Configuration

* `.env` (root) for Reddit/OpenRouter keys and Chatterbox settings.

---

## Git Hygiene

If `Orpheus-FastAPI` lives inside this repo as plain files and you **do not** want to commit models or Docker artifacts:

```gitignore
# Orpheus internals to ignore
Orpheus-FastAPI/models/
Orpheus-FastAPI/models/**
Orpheus-FastAPI/outputs/
Orpheus-FastAPI/venv/
Orpheus-FastAPI/Dockerfile*
Orpheus-FastAPI/docker-compose*.yml
Orpheus-FastAPI/docker-compose*.yaml
```

If you prefer **submodule**:

```bash
# from repo root
git submodule add https://github.com/<you>/Orpheus-FastAPI.git Orpheus-FastAPI
```

---

## Troubleshooting

* **ModuleNotFoundError** → `pip install -r requirements.txt`
* **FFmpeg not found** → install FFmpeg and ensure it’s on PATH
* **API auth errors** → check `.env` keys
* **Empty submodule folder** → `git submodule update --init --recursive`

---

## Contributing

PRs welcome: bug fixes, new voices, improved prompts, better video transitions, docs.

---

## Licenses

* **AutoScribe-AI:** MIT (see `LICENSE`)
* **Orpheus-FastAPI:** Apache‑2.0 (see `Orpheus-FastAPI/LICENSE.txt`)

When distributing together, retain both license notices.

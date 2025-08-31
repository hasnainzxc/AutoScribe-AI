# AutoScribe-AI + Orpheus TTS

AI content automation pipeline with integrated high‑performance Text‑to‑Speech. Generate character‑styled dialogues from social content and render them into short videos. Ship TTS via an OpenAI‑compatible FastAPI server with multilingual voices and emotion tags.

---

## Highlights

* Dialogue generation via OpenRouter/OpenAI
* Rick & Morty‑style prompt templates
* Google TTS or Orpheus TTS backend
* MoviePy video assembly
* Reddit ingestion with sort and time filters
* OpenAI‑compatible `/v1/audio/speech` endpoint (Orpheus)
* 24+ voices, 8 languages, emotion tags (Orpheus)
* Docker and native install paths

---

## Monorepo Structure

```
AutoScribe-AI/
├── content_generation/        # Audio/video creation
│   ├── audio_gen.py           # gTTS or Orpheus backend
│   └── video_gen.py           # MoviePy assembly
├── ingestion/
│   └── reddit_ingest.py       # Reddit API (PRAW)
├── story_generation/
│   ├── dialogue_template.py
│   ├── llm_dialogue.py
│   └── story_generator.py
├── Orpheus-FastAPI/           # TTS server (subfolder or submodule)
│   ├── app.py                 # FastAPI web + API
│   ├── tts_engine/
│   │   ├── inference.py
│   │   └── speechpipe.py
│   ├── templates/             # web UI
│   ├── static/
│   └── outputs/               # generated audio
├── create_video.py            # End‑to‑end pipeline
├── run_story_gen.py           # Story generation runner
├── requirements.txt
├── README.md                  # This file
└── .env                       # API credentials (not committed)
```

> **Note**
> If `Orpheus-FastAPI` is a **git submodule**, run after cloning:
>
> ```bash
> git submodule update --init --recursive
> ```

---

## Quick Start

### 1) Install (root env)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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
python create_video.py beermoney -n 2 -s top -t week
```

Outputs:

* `output/dialogues.json`
* `output/dialogue_X/`
* `output/final_video.mp4`

---

## TTS Backends

### A) Google TTS (default in examples)

Works out of the box via `gTTS` in `content_generation/audio_gen.py`.

### B) Orpheus TTS (FastAPI server)

![Orpheus-FASTAPI Banner](https://lex-au.github.io/Orpheus-FastAPI/Banner.png)

High‑performance TTS with OpenAI‑compatible API, multilingual voices, and emotion tags.

#### Orpheus Features

* OpenAI‑compatible `/v1/audio/speech`
* Modern web UI
* RTX‑optimized; CPU and ROCm paths supported
* 24 voices across EN/FR/DE/KO/HI/ZH/ES/IT
* Emotion tags: `<laugh>`, `<sigh>`, `<chuckle>`, etc.

#### Orpheus Project Structure (subset)

```
Orpheus-FastAPI/
├── app.py                # FastAPI server and endpoints
├── docker-compose*.yml   # Compose variants (GPU, ROCm, CPU)
├── Dockerfile.*          # Docker images
├── requirements.txt
├── templates/tts.html    # Web UI
└── tts_engine/
    ├── inference.py
    └── speechpipe.py
```

#### Orpheus: Run via Docker Compose

```bash
# create .env from example
cp .env.example .env

# (optional) switch to a language‑specific model in .env
# ORPHEUS_MODEL_NAME=Orpheus-3b-French-FT-Q8_0.gguf

# pick one
docker compose -f docker-compose-gpu.yml up         # CUDA
docker compose -f docker-compose-gpu-rocm.yml up    # ROCm
docker compose -f docker-compose-cpu.yml up         # CPU only
```

Web UI: `http://localhost:5005/`  •  API Docs: `http://localhost:5005/docs`

#### Orpheus: Native Install

```bash
cd Orpheus-FastAPI
python -m venv venv && source venv/bin/activate   # Win: venv\Scripts\activate
pip install -r requirements.txt
# choose one torch index per your GPU stack
# CUDA 12.4
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
# or ROCm nightly
# pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/rocm6.4/

mkdir -p outputs static
python app.py   # or: uvicorn app:app --host 0.0.0.0 --port 5005 --reload
```

#### Orpheus: OpenAI‑compatible API example

```bash
curl http://localhost:5005/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "orpheus",
    "input": "Hello world!",
    "voice": "tara",
    "response_format": "wav",
    "speed": 1.0
  }' \
  --output speech.wav
```

#### Voices (examples)

EN: tara, leah, jess, leo, dan, mia, zac, zoe
FR: pierre, amelie, marie
DE: jana, thomas, max
KO: 유나, 준서
HI: ऋतिका
ZH: 长乐, 白芷
ES: javi, sergio, maria
IT: pietro, giulia, carlo

> **Integration tip**
> Point `audio_gen.py` to call Orpheus instead of gTTS by toggling a config flag or env var. Keep Google TTS as fallback.

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

### Video

```bash
python content_generation/video_gen.py
```

### Full pipeline (debug)

```bash
python create_video.py beermoney -n 1 -s top -t week --debug
```

---

## Configuration

* `.env` (root) for Reddit/OpenRouter keys.
* `.env` in `Orpheus-FastAPI` for model/server settings. Example vars:

```
ORPHEUS_API_URL=http://llama-cpp-server:5006/v1/completions
ORPHEUS_API_TIMEOUT=120
ORPHEUS_MAX_TOKENS=8192
ORPHEUS_TEMPERATURE=0.6
ORPHEUS_TOP_P=0.9
ORPHEUS_SAMPLE_RATE=24000
ORPHEUS_PORT=5005
ORPHEUS_HOST=0.0.0.0
ORPHEUS_MODEL_NAME=Orpheus-3b-FT-Q8_0.gguf
```

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

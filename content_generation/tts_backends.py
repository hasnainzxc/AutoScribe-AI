from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import time

import requests
from requests import exceptions as req_exc
from config.settings import load_env


@dataclass
class TTSConfig:
    """Lightweight configuration holder for the Chatterbox TTS backend.

    Values are pulled from environment variables so users can configure
    a local or remote Chatterbox server without code changes.
    """

    # Base URL for the Chatterbox server, e.g. "http://localhost:8014"
    base_url: Optional[str] = None
    # API key to authenticate against the TTS server (if required)
    api_key: Optional[str] = None
    # Model name the TTS server expects
    model: str = "gpt-4o-mini-tts"
    # Default voices
    default_voice: str = "alloy"
    djcara_voice: str = "DJ_Caralong.mp3"
    # Response audio format requested from the server (tmp extension used in pipeline)
    response_format: str = "mp3"  # usually one of: mp3, wav, opus
    # Optional synthesis parameters (with sensible defaults)
    temperature: Optional[float] = None
    exaggeration: Optional[float] = None
    cfg_weight: Optional[float] = None
    speed_factor: Optional[float] = None
    seed: Optional[int] = None
    chunk_size: Optional[int] = None
    split_text: Optional[bool] = None
    sample_rate: Optional[int] = None
    language: Optional[str] = None

    def __init__(self) -> None:
        # Ensure .env is loaded for non-exported vars
        try:
            load_env()
        except Exception:
            pass
        # Chatterbox base URL and API key
        self.base_url = os.getenv("CHATTERBOX_BASE_URL") or None
        self.api_key = os.getenv("CHATTERBOX_API_KEY") or None

        # Model/voice/format options
        self.model = os.getenv("TTS_MODEL", self.model)
        self.default_voice = os.getenv("TTS_DEFAULT_VOICE", self.default_voice)
        self.djcara_voice = os.getenv("TTS_DJCARA_VOICE", self.djcara_voice)
        # If Chatterbox is configured, prefer WAV for tmp files (server outputs WAV)
        default_fmt = "wav" if (self.base_url and "8014" in self.base_url) else self.response_format
        self.response_format = os.getenv("TTS_RESPONSE_FORMAT", default_fmt)

        # Optional tuning params
        def _f(k: str, default: Optional[float] = None) -> Optional[float]:
            v = os.getenv(k)
            try:
                return float(v) if v is not None and v != "" else default
            except Exception:
                return default
        def _i(k: str, default: Optional[int] = None) -> Optional[int]:
            v = os.getenv(k)
            try:
                return int(v) if v is not None and v != "" else default
            except Exception:
                return default
        def _b(k: str, default: Optional[bool] = None) -> Optional[bool]:
            v = os.getenv(k)
            if v is None:
                return default
            s = v.strip().lower()
            if s in {"1", "true", "yes", "on"}:
                return True
            if s in {"0", "false", "no", "off"}:
                return False
            return default

        # Defaults if not provided in env
        self.temperature = _f("TTS_TEMP", 0.6)
        self.exaggeration = _f("TTS_EXAG", 0.9)
        # Accept both TTS_CFG and TTS_CFG_WEIGHT; prefer weight name
        cfgw = os.getenv("TTS_CFG_WEIGHT") or os.getenv("TTS_CFG")
        try:
            self.cfg_weight = float(cfgw) if cfgw else 0.3
        except Exception:
            self.cfg_weight = 0.3
        # Accept both TTS_SPEED and TTS_SPEED_FACTOR; prefer speed factor name
        spdf = os.getenv("TTS_SPEED_FACTOR") or os.getenv("TTS_SPEED")
        try:
            self.speed_factor = float(spdf) if spdf else 1.0
        except Exception:
            self.speed_factor = 1.0
        self.seed = _i("TTS_SEED", 2024)
        self.chunk_size = _i("TTS_CHUNK_SIZE", None)
        self.split_text = _b("TTS_SPLIT_TEXT", True)
        self.sample_rate = _i("TTS_SAMPLE_RATE", 24000)
        self.language = os.getenv("TTS_LANGUAGE") or None


class ChatterboxTTSBackend:
    """Chatterbox TTS HTTP client.

    Uses documented endpoints:
      - GET  /get_predefined_voices
      - POST /tts
      - GET  /api/outputs?limit=... [&prefix=...]
      - GET  /outputs/<filename>
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, cfg: Optional[TTSConfig] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.name = "Chatterbox"
        # Carry computed defaults (format, chunking, tuning) from TTSConfig
        self._cfg = cfg or TTSConfig()

    # ---------- REST helpers ----------
    def _headers(self) -> Dict[str, str]:
        h = {"accept": "application/json"}
        if self.api_key:
            # If server expects different auth header, adjust here
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def list_predefined_voices(self) -> List[Dict[str, str]]:
        url = f"{self.base_url}/get_predefined_voices"
        print(f"[Chatterbox] GET {url}")
        resp = requests.get(url, headers=self._headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return []
        return [
            {"display_name": v.get("display_name", ""), "filename": v.get("filename", "")}
            for v in data
            if isinstance(v, dict)
        ]

    def _latest_output(self, prefix: Optional[str] = None) -> Optional[Dict[str, Any]]:
        params = {"limit": 1}
        if prefix:
            params["prefix"] = prefix
        url = f"{self.base_url}/api/outputs"
        try:
            # No client-side timeout by default; rely on server behavior
            resp = requests.get(url, params=params, headers=self._headers())
            resp.raise_for_status()
            items = resp.json()
            if isinstance(items, list) and items:
                return items[0]
            return None
        except req_exc.RequestException as e:
            # Transient network/server issue; treat as no result and continue polling
            print(f"[Chatterbox] outputs fetch error: {e}; continuing to wait...")
            return None

    def _download_output(self, item: Dict[str, Any], out_path: str) -> str:
        rel = item.get("url") or f"/outputs/{item.get('filename')}"
        url = f"{self.base_url}{rel}"
        print(f"[Chatterbox] Downloading: {url}")
        attempts = int(os.getenv("CHATTERBOX_DOWNLOAD_RETRIES", "0"))  # 0 => infinite retries
        last_err: Optional[Exception] = None
        i = 0
        while attempts <= 0 or i < attempts:
            i += 1
            try:
                r = requests.get(url, headers=self._headers())
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"[Chatterbox] Saved: {out_path} ({len(r.content)} bytes)")
                return out_path
            except req_exc.RequestException as e:
                last_err = e
                if attempts > 0:
                    print(f"[Chatterbox] Download attempt {i}/{attempts} failed: {e}")
                else:
                    print(f"[Chatterbox] Download attempt {i} failed: {e}; retrying...")
                time.sleep(1.5)
        raise RuntimeError(f"Failed to download output after {attempts} attempts: {last_err}")

    # ---------- Synthesis ----------
    def synthesize(
        self,
        text: str,
        out_path: str,
        voice: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Determine a reasonable voice default if not provided
        voice = voice or "DJ_Caralong.mp3"
        # Use voice stem as prefix to filter outputs
        voice_prefix = Path(voice).stem if voice else None

        # Snapshot latest before request to detect new file
        before = self._latest_output(prefix=voice_prefix)
        before_name = before.get("filename") if before else None

        # POST /tts with text and voice filename
        url = f"{self.base_url}/tts"
        # Auto-scale chunk size if not provided: larger texts get bigger chunks
        auto_chunk = 120
        L = len(text or "")
        if L > 2400:
            auto_chunk = 360
        elif L > 1200:
            auto_chunk = 240

        body: Dict[str, Any] = {
            "text": text,
            "voice_mode": "predefined",
            "predefined_voice_id": voice,
            "output_format": (self._cfg.response_format or "wav").lower(),
            "split_text": True if self._cfg.split_text is None else bool(self._cfg.split_text),
            "chunk_size": int(self._cfg.chunk_size or auto_chunk),
        }
        # Merge optional tuning parameters (CLI/env)
        if params:
            if params.get("temperature") is not None:
                body["temperature"] = float(params["temperature"])  # type: ignore[arg-type]
            if params.get("exaggeration") is not None:
                body["exaggeration"] = float(params["exaggeration"])  # type: ignore[arg-type]
            # Accept cfg or cfg_weight
            if params.get("cfg_weight") is not None:
                body["cfg_weight"] = float(params["cfg_weight"])  # type: ignore[arg-type]
            elif params.get("cfg") is not None:
                body["cfg_weight"] = float(params["cfg"])  # type: ignore[arg-type]
            # Accept speed or speed_factor
            if params.get("speed_factor") is not None:
                body["speed_factor"] = float(params["speed_factor"])  # type: ignore[arg-type]
            elif params.get("speed") is not None:
                body["speed_factor"] = float(params["speed"])  # type: ignore[arg-type]
            if params.get("seed") is not None:
                body["seed"] = int(params["seed"])  # type: ignore[arg-type]
            if params.get("language"):
                body["language"] = str(params["language"])  # type: ignore[arg-type]
        else:
            # Fall back to config/env defaults
            body["temperature"] = self._cfg.temperature
            body["exaggeration"] = self._cfg.exaggeration
            body["cfg_weight"] = self._cfg.cfg_weight
            body["speed_factor"] = self._cfg.speed_factor
            body["seed"] = self._cfg.seed
            if self._cfg.language:
                body["language"] = self._cfg.language
            if self._cfg.sample_rate:
                body["sample_rate"] = self._cfg.sample_rate
        print(f"[Chatterbox] POST {url} voice={voice} text_len={len(text)}")
        # No client-side timeout: rely on server-side timeouts and polling
        try:
            resp = requests.post(
                url,
                json=body,
                headers=self._headers(),
            )
            if resp.status_code >= 400:
                # Likely a bad request (e.g., wrong voice id); surface immediately
                raise RuntimeError(
                    f"Chatterbox TTS failed: HTTP {resp.status_code} {resp.text[:200]}"
                )
        except req_exc.RequestException as e:
            # Non-fatal: proceed to poll regardless of POST read/connect outcome
            print(f"[Chatterbox] POST exception ({e}); proceeding to poll for output...")

        # Poll for a new output file
        start = time.time()
        # Infinite polling by default; can set CHATTERBOX_POLL_TIMEOUT to cap
        timeout_env = os.getenv("CHATTERBOX_POLL_TIMEOUT", "")
        timeout_s = int(timeout_env) if timeout_env.isdigit() else None
        poll_interval = float(os.getenv("CHATTERBOX_POLL_INTERVAL", "1.0"))
        candidate: Optional[Dict[str, Any]] = None
        next_log = 0
        verbose = os.getenv("CHATTERBOX_VERBOSE_POLL", "").strip().lower() in {"1", "true", "yes"}
        while True:
            time.sleep(poll_interval)
            latest = self._latest_output(prefix=voice_prefix)
            if latest and latest.get("filename") != before_name:
                candidate = latest
                break
            # periodic status log
            elapsed = int(time.time() - start)
            if elapsed >= next_log:
                if verbose and latest:
                    fname = latest.get("filename")
                    sz = latest.get("size_bytes")
                    mod = latest.get("modified")
                    try:
                        kb = f"{int(sz)//1024}KB" if isinstance(sz, int) else str(sz)
                    except Exception:
                        kb = str(sz)
                    print(
                        f"[Chatterbox] Poll {elapsed}s — waiting for prefix '{voice_prefix}'. "
                        f"latest=({fname}, {kb}, {mod}), last_seen={before_name}"
                    )
                else:
                    if timeout_s is not None:
                        print(
                            f"[Chatterbox] Polling outputs (elapsed {elapsed}s/{timeout_s}s) — waiting for new file with prefix '{voice_prefix}', last_seen={before_name}"
                        )
                    else:
                        print(
                            f"[Chatterbox] Polling outputs (elapsed {elapsed}s) — waiting for new file with prefix '{voice_prefix}', last_seen={before_name}"
                        )
                next_log = elapsed + 5
            if timeout_s is not None and elapsed >= timeout_s:
                print(
                    f"[Chatterbox] Reached poll timeout ({timeout_s}s) without a new file; stopping."
                )
                break

        # Download to out_path
        return self._download_output(candidate, out_path)


def get_tts_backend() -> Optional[ChatterboxTTSBackend]:
    """Return a configured TTS backend if environment is set, otherwise None.

    This allows the rest of the pipeline to fall back to gTTS when no
    server‑based TTS is available.
    """
    cfg = TTSConfig()
    # Require base_url to enable server TTS
    if not cfg.base_url:
        print("[TTS] No server base URL configured. Set CHATTERBOX_BASE_URL=http://localhost:8014")
        return None
    return ChatterboxTTSBackend(cfg.base_url, cfg.api_key, cfg)

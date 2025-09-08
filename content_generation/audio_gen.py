"""Audio generation module for creating voice clips from dialogue.

This module uses gTTS (Google Text to Speech) to create audio files from
the Rick and Morty dialogue. It supports different voices for different
characters and includes Rick's signature burps.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import re
import datetime as _dt
from gtts import gTTS

try:
    from pydub import AudioSegment  # type: ignore
    _PYDUB_AVAILABLE = True
except Exception:
    AudioSegment = None  # type: ignore
    _PYDUB_AVAILABLE = False

from .tts_backends import get_tts_backend, TTSConfig


def _persona_default_tts_params(label: Optional[str], cfg: TTSConfig) -> Dict[str, object]:
    """Return conservative, clarity-focused defaults per persona.

    Defaults aim to keep slang/style but slow pacing slightly to avoid
    "eating words" while preserving energy.
    """
    lbl = (label or "").strip().lower()
    if lbl == "djcara":
        params: Dict[str, object] = {}
        if cfg.djcara_temperature is not None:
            params["temperature"] = cfg.djcara_temperature
        if cfg.djcara_exaggeration is not None:
            params["exaggeration"] = cfg.djcara_exaggeration
        if cfg.djcara_speed_factor is not None:
            params["speed_factor"] = cfg.djcara_speed_factor
        if getattr(cfg, "djcara_cfg_weight", None) is not None:
            params["cfg_weight"] = cfg.djcara_cfg_weight  # type: ignore[attr-defined]
        if getattr(cfg, "djcara_seed", None) is not None:
            params["seed"] = cfg.djcara_seed  # type: ignore[attr-defined]
        if cfg.djcara_chunk_size is not None:
            params["chunk_size"] = cfg.djcara_chunk_size
        return params
    return {}


def _merge_params(base: Dict[str, object], override: Optional[Dict]) -> Dict[str, object]:
    merged = {**base}
    if override:
        merged.update({k: v for k, v in override.items() if v is not None})
    return merged


def _is_valid_mp3(path: str) -> bool:
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 1024:
            return False
        if _PYDUB_AVAILABLE:
            # Attempt light decode init
            _ = AudioSegment.from_file(path, format="mp3")
        return True
    except Exception:
        return False


def create_dialogue_audio(
    dialogue: List[str],
    output_dir: str,
    voice_override: Optional[str] = None,
    force_gtts: bool = False,
    tts_params: Optional[Dict] = None,
) -> List[str]:
    """Create audio files for each line of dialogue.
    
    Args:
        dialogue: List of dialogue lines
        output_dir: Directory to save audio files
        
    Returns:
        List of paths to created audio files
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []
    
    print(f"\n[Audio Generation] Processing {len(dialogue)} lines of dialogue...")
    
    # Select TTS backend once per batch
    backend = None if force_gtts else get_tts_backend()
    cfg = TTSConfig()

    for i, line in enumerate(dialogue):
        if not isinstance(line, str):
            print(f"[Audio Generation] Warning: Invalid line format at index {i}. Converting to string.")
            line = str(line)

        # Determine speaker by prefix if present
        speaker = None
        prefix = line.split(":", 1)[0].strip().lower() if ":" in line else ""
        if prefix in {"rick"}:
            speaker = "rick"
        elif prefix in {"morty"}:
            speaker = "morty"
        elif prefix in {"djcara", "dj cara", "cara"}:
            speaker = "djcara"

        label = speaker or "speaker"
        print(f"[Audio Generation] Processing line {i+1}: {label.capitalize()}")

        # Clean up the line - remove character name and clean up burps
        clean_line = (
            line.replace("Rick: ", "").replace("Morty: ", "")
                .replace("DJCARA: ", "").replace("DJ Cara: ", "").replace("Cara: ", "")
        )
        if speaker == "rick":
            # For Rick's lines, we'll need to split around the burps
            # and create separate audio files that we'll merge
            parts = clean_line.split("*burp*")
            clean_line = " ".join(parts)

        # Save with character prefix for easier identification
        character = speaker or "speaker"
        filename = f"{character}_line_{i}.mp3"
        filepath = os.path.join(output_dir, filename)
        # Choose voice depending on speaker (if server backend is active)
        # Persona-aware default tuning
        persona_defaults: Dict[str, object] = _persona_default_tts_params(speaker, cfg)
        params = _merge_params(persona_defaults, tts_params)
        if voice_override:
            voice = voice_override
        elif character == "djcara":
            voice = cfg.djcara_voice
        else:
            voice = cfg.default_voice
        wrote = False
        try:
            if backend is not None:
                # Pass merged params to backend (helps clarity for DJ Cara)
                backend.synthesize(clean_line, filepath, voice=voice, params=params)
                wrote = True
        except Exception as e:
            print(f"[TTS] Backend failed, falling back to gTTS: {e}")
        # Validate and/or fallback to gTTS
        if (not wrote) or (not _is_valid_mp3(filepath)):
            try:
                # If falling back for DJ Cara, prefer slightly slower gTTS pacing
                tts = gTTS(text=clean_line, lang='en', slow=(speaker == "djcara"))
                tts.save(filepath)
                wrote = True
            except Exception as e:
                print(f"[TTS] gTTS fallback failed: {e}")
                wrote = False
        if not wrote or (not _is_valid_mp3(filepath)):
            print(f"[TTS] Skipping invalid audio for line {i+1}")
            continue
        audio_files.append(filepath)
    
    return audio_files


def _sanitize_filename(text: str, max_len: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("/", "-")
    text = re.sub(r"[^a-z0-9\- _.]", "", text)
    text = text.replace(" ", "_")
    return text[:max_len] if len(text) > max_len else text


def _ordinal(n: int) -> str:
    return "%d%s" % (
        n,
        "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
    )


def _today_token() -> str:
    now = _dt.datetime.now()
    return f"{now.day:02d} {now.strftime('%b').lower()}_"


def _group_line_files_by_speaker(files: List[str], default_speaker: Optional[str] = None) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for fp in files:
        base = os.path.basename(fp)
        if base.startswith("rick_"):
            groups.setdefault("rick", []).append(fp)
        elif base.startswith("morty_"):
            groups.setdefault("morty", []).append(fp)
        else:
            # unknown speaker, bucket under default or generic label
            key = (default_speaker or "speaker").lower()
            groups.setdefault(key, []).append(fp)
    # keep order
    for k in groups:
        groups[k] = sorted(groups[k])
    return groups


def _unique_speakers_in_order(files: List[str], default_speaker: Optional[str] = None) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for fp in files:
        base = os.path.basename(fp)
        if base.startswith("rick_"):
            s = "rick"
        elif base.startswith("morty_"):
            s = "morty"
        else:
            s = (default_speaker or "speaker").lower()
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered

def _combine_mp3s(file_list: List[str], output_path: str) -> str:
    if not file_list:
        raise ValueError("No files to combine")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if _PYDUB_AVAILABLE:
        combined = AudioSegment.empty()
        for fp in file_list:
            seg = AudioSegment.from_file(fp, format="mp3")
            combined += seg
        combined.export(output_path, format="mp3")
        return output_path
    # Fallback: use ffmpeg concat demuxer
    import tempfile, subprocess
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        for fp in file_list:
            f.write(f"file '{os.path.abspath(fp)}'\n")
        list_path = f.name
    try:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            output_path,
        ]
        subprocess.run(cmd, check=True)
        return output_path
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass


def render_combined_audio(
    dialogue: List[str],
    title: str,
    audio_dir: str,
    date_token: Optional[str] = None,
    default_speaker: Optional[str] = None,
    cleanup_parts: bool = True,
    single_track: bool = False,
    label: Optional[str] = None,
    voice_override: Optional[str] = None,
    tts_params: Optional[Dict] = None,
) -> List[str]:
    """Render a dialogue into combined MP3s per speaker with consistent naming.

    - Generates per-line MP3s to a temp subdir
    - Groups by speaker and concatenates to a single MP3 per speaker
    - Saves final files under `audio_dir`

    Returns list of final MP3 paths.
    """
    audio_root = Path(audio_dir)
    audio_root.mkdir(parents=True, exist_ok=True)
    date_token = date_token or _today_token()
    safe_title = _sanitize_filename(title)

    # If single_track is requested, try one-shot synthesis for the entire text
    if single_track:
        # Build a continuous script by stripping prefixes and joining lines
        cleaned_lines: List[str] = []
        for ln in dialogue:
            if not isinstance(ln, str):
                ln = str(ln)
            s = (
                ln.replace("Rick: ", "").replace("Morty: ", "")
                  .replace("DJCARA: ", "").replace("DJ Cara: ", "").replace("Cara: ", "")
            ).strip()
            if s:
                cleaned_lines.append(s)
        # If user passed a single monologue string (via wrapper), this stays intact
        script = "\n".join(cleaned_lines)

        # Choose label and voice
        out_label = _sanitize_filename(label or default_speaker or "dialogue")
        cfg = TTSConfig()
        voice = voice_override or (cfg.djcara_voice if out_label == "djcara" else cfg.default_voice)
        # Merge persona-aware defaults (e.g., slower pacing for DJ Cara)
        persona_defaults = _persona_default_tts_params(out_label, cfg)
        eff_params = _merge_params(persona_defaults, tts_params)

        # Decide tmp extension based on server format; final is mp3 for consistency
        tmp_ext = (cfg.response_format or "wav").lower()
        existing = [p for p in os.listdir(audio_root) if p.startswith(f"{out_label}_") and (f"_{date_token}" in p) and p.endswith(".mp3")]
        ord_token = _ordinal(len(existing) + 1)
        base_name = f"{out_label}_{safe_title}_{date_token}{ord_token}"
        out_mp3 = str(audio_root / f"{base_name}.mp3")
        out_wav = str(audio_root / f"{base_name}.wav")
        tmp_dir = audio_root / ".tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_raw = str(tmp_dir / f"{base_name}.{tmp_ext}")

        wrote = False
        try:
            backend = get_tts_backend()
            if backend is None:
                raise RuntimeError("No server TTS configured; use gTTS fallback")
            name = getattr(backend, "name", backend.__class__.__name__)
            print(f"[TTS] Synthesizing single track via {name} with voice '{voice}'...")
            # Pass optional tuning params through to the backend
            try:
                backend.synthesize(script, tmp_raw, voice=voice, params=eff_params)  # type: ignore[call-arg]
            except TypeError:
                # Backward-compat if backend doesn't accept params
                backend.synthesize(script, tmp_raw, voice=voice)
            wrote = True
        except Exception as e:
            print(f"[TTS] Single-track backend failed, falling back to gTTS: {e}")
        # Convert/validate and fallback
        try:
            if wrote and os.path.exists(tmp_raw):
                if tmp_ext != "mp3":
                    if _PYDUB_AVAILABLE:
                        seg = AudioSegment.from_file(tmp_raw)
                        seg.export(out_mp3, format="mp3")
                    else:
                        # No converter available: keep WAV as final artifact
                        os.replace(tmp_raw, out_wav)
                else:
                    # tmp is already mp3
                    os.replace(tmp_raw, out_mp3)
        except Exception as e:
            print(f"[TTS] Conversion to mp3 failed: {e}")

        # Decide final output path:
        final_out: str = ""
        if os.path.exists(out_mp3) and _is_valid_mp3(out_mp3):
            final_out = out_mp3
        elif os.path.exists(out_wav):
            final_out = out_wav
        else:
            # No valid server output; fallback to gTTS unless explicitly disabled
            if os.getenv("TTS_REQUIRE_SERVER", "").strip().lower() in {"1", "true", "yes"}:
                raise RuntimeError(
                    "Server TTS required but not available. Set CHATTERBOX_BASE_URL=http://localhost:8014 "
                    "or unset TTS_REQUIRE_SERVER to allow gTTS fallback."
                )
            try:
                # For DJ Cara fallback, use slower gTTS pacing for clarity
                tts = gTTS(text=script, lang='en', slow=(out_label == "djcara"))
                tts.save(out_mp3)
                final_out = out_mp3
            except Exception as e:
                raise RuntimeError(f"TTS failed for single-track synthesis: {e}")

        # Cleanup tmp
        try:
            if os.path.exists(tmp_raw):
                os.remove(tmp_raw)
            # best-effort remove tmp dir
            for root, dirs, files in os.walk(tmp_dir, topdown=False):
                for name in files:
                    try:
                        os.remove(Path(root) / name)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(Path(root) / name)
                    except Exception:
                        pass
            os.rmdir(tmp_dir)
        except Exception:
            pass

        return [final_out]

    # Generate raw line audio into a tmp folder (multi-track combine path)
    tmp = audio_root / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    line_files = create_dialogue_audio(dialogue, str(tmp), voice_override=voice_override, tts_params=tts_params)
    if not line_files:
        print("[TTS] No valid line audio produced; forcing gTTS for all lines...")
        line_files = create_dialogue_audio(dialogue, str(tmp), voice_override=None, force_gtts=True, tts_params=tts_params)
    if not line_files:
        raise RuntimeError("TTS failed to produce any valid audio lines")

    final_paths: List[str] = []
    # Compute per-label ordinal based on existing files for the date
    def next_ordinal_for(prefix_label: str) -> str:
        prefix = f"{prefix_label}_"
        suffix = f"_{date_token}"
        existing = [
            p for p in os.listdir(audio_root)
            if p.startswith(prefix) and (suffix in p) and p.endswith(".mp3")
        ]
        return _ordinal(len(existing) + 1)

    if single_track:
        speakers = _unique_speakers_in_order(line_files, default_speaker)
        prefix_label = _sanitize_filename(label) if label else ("-".join(speakers) if speakers else (default_speaker or "dialogue"))
        ord_token = next_ordinal_for(prefix_label)
        fname = f"{prefix_label}_{safe_title}_{date_token}{ord_token}.mp3"
        out_path = str(audio_root / fname)
        _combine_mp3s(line_files, out_path)
        final_paths.append(out_path)
    else:
        grouped = _group_line_files_by_speaker(line_files, default_speaker=default_speaker)
        for character, files in grouped.items():
            ord_token = next_ordinal_for(character)
            fname = f"{character}_{safe_title}_{date_token}{ord_token}.mp3"
            out_path = str(audio_root / fname)
            _combine_mp3s(files, out_path)
            final_paths.append(out_path)

    if cleanup_parts:
        # remove tmp line files for cleanliness
        try:
            for fp in line_files:
                os.remove(fp)
            # attempt to remove tmp dir if empty
            for root, dirs, files in os.walk(tmp, topdown=False):
                for name in files:
                    try:
                        os.remove(Path(root) / name)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(Path(root) / name)
                    except Exception:
                        pass
            os.rmdir(tmp)
        except Exception:
            pass

    return final_paths


def render_single_track_text(
    script: str,
    title: str,
    audio_dir: str,
    label: Optional[str] = None,
    voice_override: Optional[str] = None,
    tts_params: Optional[Dict] = None,
) -> List[str]:
    """Synthesize a single monologue to one MP3 using the server TTS if available,
    otherwise fall back to gTTS.

    Thin wrapper that routes through the single‑track path with minimal cleanup.
    """
    # We reuse the single‑track implementation by passing a one‑element list
    # and setting the label to ensure file naming uses the character label.
    dialogue = [script]
    return render_combined_audio(
        dialogue,
        title,
        audio_dir,
        default_speaker=label or "dialogue",
        cleanup_parts=True,
        single_track=True,
        label=label,
        voice_override=voice_override,
        tts_params=tts_params,
    )

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Create audio files from dialogue")
    parser.add_argument("dialogue_file", help="JSON file containing dialogue")
    parser.add_argument(
        "-o", 
        "--output-dir", 
        default="audio_output",
        help="Directory to save audio files (default: audio_output)"
    )
    
    args = parser.parse_args()
    
    with open(args.dialogue_file) as f:
        dialogues = json.load(f)
    
    for i, dialogue in enumerate(dialogues):
        output_dir = os.path.join(args.output_dir, f"dialogue_{i}")
        audio_files = create_dialogue_audio(dialogue, output_dir)
        print(f"Created {len(audio_files)} audio files in {output_dir}")

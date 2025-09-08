from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Dict

try:
    from pydub import AudioSegment  # type: ignore
    _PYDUB_AVAILABLE = True
except Exception:
    AudioSegment = None  # type: ignore
    _PYDUB_AVAILABLE = False


def _list_audio_files(dir_path: str) -> List[str]:
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        return []
    exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
    files = [str(fp) for fp in p.iterdir() if fp.is_file() and fp.suffix.lower() in exts]
    return sorted(files)


def pick_intro_outro(intro_dir: Optional[str] = None, outro_dir: Optional[str] = None, intro_outro_dir: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """Pick first intro and outro files from provided dirs or environment.

    Priority:
      1) Explicit intro_dir/outro_dir if provided
      2) INTRO_OUTRO_DIR env (try files with names containing 'intro'/'outro')
      3) INTRO_DIR / OUTRO_DIR env
      4) Defaults: ./intro and ./outro
    """
    import os
    # Load .env so INTRO_* variables are available when not exported
    try:
        from config.settings import load_env  # lazy import to avoid cycles
        load_env()
    except Exception:
        pass
    idir = intro_dir or intro_outro_dir or os.getenv("INTRO_DIR") or os.getenv("INTRO_OUTRO_DIR") or "intro"
    odir = outro_dir or intro_outro_dir or os.getenv("OUTRO_DIR") or os.getenv("INTRO_OUTRO_DIR") or "outro"
    intro_files = _list_audio_files(idir)
    outro_files = _list_audio_files(odir)
    # If nothing found, try a common repo-local folder named 'intro_outros'
    if not intro_files and not outro_files:
        guessed = str(Path.cwd() / "intro_outros")
        if Path(guessed).exists():
            intro_outro_dir = guessed
            idir = odir = guessed
            intro_files = _list_audio_files(idir)
            outro_files = _list_audio_files(odir)
    # If a unified folder was used, try to pick by filename hint
    if intro_outro_dir and intro_outro_dir == idir == odir:
        intro_hint = [f for f in intro_files if "intro" in Path(f).name.lower()]
        outro_hint = [f for f in outro_files if "outro" in Path(f).name.lower()]
        intro = (intro_hint[0] if intro_hint else (intro_files[0] if intro_files else None))
        outro = (outro_hint[0] if outro_hint else (outro_files[0] if outro_files else None))
        return intro, outro
    intro = intro_files[0] if intro_files else None
    outro = outro_files[0] if outro_files else None
    return intro, outro


def combine_with_intro_outro(
    main_file: str,
    intro_file: Optional[str],
    outro_file: Optional[str],
    output_file: Optional[str] = None,
    *,
    crossfade_ms: int = 0,
    bridge_file: Optional[str] = None,
) -> str:
    """Create a new MP3 that concatenates intro + main + outro.

    Uses pydub when available; otherwise, requires that all inputs are MP3 and uses ffmpeg concat.
    """
    main_path = Path(main_file)
    out_path = Path(output_file) if output_file else main_path.with_name(main_path.stem + "_with_intro_outro.mp3")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if _PYDUB_AVAILABLE:
        segs: List[AudioSegment] = []
        if intro_file:
            segs.append(AudioSegment.from_file(intro_file))
        if bridge_file:
            segs.append(AudioSegment.from_file(bridge_file))
        segs.append(AudioSegment.from_file(main_file))
        if outro_file:
            segs.append(AudioSegment.from_file(outro_file))
        combined = segs[0]
        for s in segs[1:]:
            if crossfade_ms > 0:
                combined = combined.append(s, crossfade=crossfade_ms)
            else:
                combined += s
        combined.export(str(out_path), format="mp3")
        return str(out_path)

    # Fallback path: require MP3s and use ffmpeg concat demuxer
    if any(Path(f).suffix.lower() != ".mp3" for f in [x for x in [intro_file, main_file, outro_file] if x]):
        raise RuntimeError("Intro/outro combine requires pydub (ffmpeg) unless all inputs are MP3")

    import tempfile, subprocess
    parts: List[str] = []
    if intro_file:
        parts.append(os.path.abspath(intro_file))
    if bridge_file:
        parts.append(os.path.abspath(bridge_file))
    parts.append(os.path.abspath(main_file))
    if outro_file:
        parts.append(os.path.abspath(outro_file))
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        for fp in parts:
            f.write(f"file '{fp}'\n")
        list_path = f.name
    try:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        return str(out_path)
    except subprocess.CalledProcessError:
        # Re-encode fallback to handle mismatched codecs/bitrates
        inputs = []
        if intro_file:
            inputs.append(os.path.abspath(intro_file))
        if bridge_file:
            inputs.append(os.path.abspath(bridge_file))
        inputs.append(os.path.abspath(main_file))
        if outro_file:
            inputs.append(os.path.abspath(outro_file))
        # Build filter_complex concat
        fc_in = "".join(f"[{i}:a]" for i in range(len(inputs)))
        filter_complex = f"{fc_in}concat=n={len(inputs)}:v=0:a=1[a]"
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
        ]
        for inp in inputs:
            cmd += ["-i", inp]
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[a]",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        return str(out_path)
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass


def apply_intro_outro_to_files(
    files: List[str],
    intro_dir: Optional[str] = None,
    outro_dir: Optional[str] = None,
    *,
    intro_outro_dir: Optional[str] = None,
    crossfade_ms: int = 0,
    bridge_text: Optional[str] = None,
    voice_override: Optional[str] = None,
    tts_params: Optional[Dict] = None,
    label: Optional[str] = None,
) -> List[str]:
    intro, outro = pick_intro_outro(intro_dir=intro_dir, outro_dir=outro_dir, intro_outro_dir=intro_outro_dir)
    if not intro and not outro:
        print(f"[Intro/Outro] No audio found in '{intro_dir}' or '{outro_dir}'. Skipping.")
        return files
    results: List[str] = []
    for fp in files:
        bridge_file: Optional[str] = None
        # If a bridge text is provided, synthesize a short snippet in the same folder
        if bridge_text:
            try:
                from .audio_gen import render_single_track_text  # lazy import to avoid cycles
                out_dir = str(Path(fp).parent)
                title_stub = "bridge"
                # Use the provided label to pick persona defaults
                label_used = (label or "djcara")
                paths = render_single_track_text(
                    bridge_text.strip(),
                    title_stub,
                    out_dir,
                    label=label_used,
                    voice_override=voice_override,
                    tts_params=tts_params,
                )
                bridge_file = paths[0] if paths else None
            except Exception as e:
                print(f"[Intro/Outro] Bridge synthesis failed: {e}")
                bridge_file = None
        out = combine_with_intro_outro(fp, intro, outro, crossfade_ms=crossfade_ms, bridge_file=bridge_file)
        results.append(out)
        print(f"[Intro/Outro] Created: {out}")
        # Cleanup bridge file if it exists and is distinct
        try:
            if bridge_file and os.path.exists(bridge_file):
                os.remove(bridge_file)
        except Exception:
            pass
    return results

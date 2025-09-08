from story_generation.story_generator import create_stories
from content_generation.audio_gen import render_combined_audio, render_single_track_text
from content_generation.intro_outro import apply_intro_outro_to_files
from content_generation.tts_backends import get_tts_backend, TTSConfig

import argparse
import json
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate audio dialogues from subreddit posts (audio-only)")
    parser.add_argument("subreddit", nargs="?", default="beermoney", help="Subreddit to fetch from (default: beermoney)")
    parser.add_argument("-n", "--number", type=int, default=1, help="Backwards-compat only; ignored (always processes 1 post)")
    parser.add_argument("-s", "--sort", choices=["hot", "new", "rising", "top"], default="top", help="Sort order (default: top)")
    parser.add_argument("-t", "--time-filter", choices=["all", "year", "month", "week", "day", "hour"], default="day", help="Time filter for 'top' (default: day)")
    parser.add_argument("-o", "--output", default="output", help="Audio output directory (default: output)")
    parser.add_argument("--default-speaker", default=None, help="Label to use if lines have no 'Name:' prefix (single-speaker flows)")
    parser.add_argument("-c", "--character", choices=["rickmorty", "djcara"], default=None, help="Character style for generation (if omitted, you will be prompted)")
    parser.add_argument("--tts-voice", default=None, help="Override TTS voice name for this run (applies to all lines)")
    parser.add_argument("--list-voices", action="store_true", help="List predefined voices from Chatterbox and exit")
    parser.add_argument("--cara", action="store_true", help="Explicitly use Non Stop Pop voice (Non_Stop_Pop.mp3)")
    # Intro/outro options
    parser.add_argument("--with-intro-outro", action="store_true", help="Automatically add intro/outro (no prompt)")
    parser.add_argument("--without-intro-outro", action="store_true", help="Do not add intro/outro (no prompt)")
    parser.add_argument("--intro-dir", default=None, help="Directory containing intro audio")
    parser.add_argument("--outro-dir", default=None, help="Directory containing outro audio")
    parser.add_argument("--intro-outro-dir", default=None, help="Single directory containing intro/outro stingers")
    parser.add_argument("--crossfade-ms", type=int, default=None, help="Crossfade milliseconds between segments (requires pydub)")
    parser.add_argument("--with-bridge", action="store_true", help="Insert a short generated intro line between intro and main audio")
    parser.add_argument("--without-bridge", action="store_true", help="Do not insert a generated intro line")
    # Optional TTS tuning
    parser.add_argument("--tts-temp", type=float, default=None, help="TTS temperature (e.g., 0.6)")
    parser.add_argument("--tts-exag", type=float, default=None, help="TTS exaggeration (e.g., 0.9)")
    parser.add_argument("--tts-cfg", type=float, default=None, help="TTS CFG weight (e.g., 0.3)")
    parser.add_argument("--tts-cfg-weight", type=float, default=None, help="Alias for --tts-cfg")
    parser.add_argument("--tts-speed", type=float, default=None, help="TTS speaking speed multiplier (e.g., 1.0)")
    parser.add_argument("--tts-speed-factor", type=float, default=None, help="Alias for --tts-speed")
    parser.add_argument("--tts-seed", type=int, default=None, help="TTS generation seed (e.g., 2024)")

    args = parser.parse_args()

    # Backwards-compat note
    if args.number != 1:
        print("[Info] -n/--number is ignored; processing exactly 1 post.")

    # Optional: list Chatterbox voices and exit
    if args.list_voices:
        backend = get_tts_backend()
        if backend is None or not hasattr(backend, "list_predefined_voices"):
            print("No Chatterbox backend detected. Set CHATTERBOX_BASE_URL=http://localhost:8014")
            raise SystemExit(1)
        voices = backend.list_predefined_voices()  # type: ignore[attr-defined]
        if not voices:
            print("No predefined voices returned.")
            raise SystemExit(0)
        print("Predefined voices:")
        for idx, v in enumerate(voices, start=1):
            print(f"{idx:02d}. display_name={v.get('display_name','')}  filename={v.get('filename','')}")
        raise SystemExit(0)

    print("[1/3] Fetching and generating story...")
    if args.cara and not args.tts_voice:
        args.tts_voice = "Non_Stop_Pop.mp3"

    # Interactive character selection if not provided
    def _choose_character(default: str = "rickmorty") -> str:
        try:
            print("Choose a character style:")
            print("  1) rickmorty (dialogue)\n  2) djcara (single monologue)")
            ans = input(f"Selection [1/2] (default {default}): ").strip().lower()
        except EOFError:
            return default
        if ans in {"1", "rick", "rickmorty"}:
            return "rickmorty"
        if ans in {"2", "djcara", "cara", "dj"}:
            return "djcara"
        if not ans:
            return default
        # fallback to default on unrecognized input
        return default

    character = args.character or _choose_character()

    # If DJ Cara, ask for generation mode (Reddit story vs. Cara demo)
    def _choose_mode(default: str = "reddit") -> str:
        try:
            print("Choose generation mode:")
            print("  1) reddit story (from subreddit)")
            print("  2) cara demo (original lines)")
            ans = input(f"Selection [1/2] (default {default}): ").strip().lower()
        except EOFError:
            return default
        if ans in {"1", "reddit", "story"}:
            return "reddit"
        if ans in {"2", "demo", "cara"}:
            return "demo"
        if not ans:
            return default
        return default

    mode = "reddit"
    if character == "djcara":
        mode = _choose_mode()

    # Build TTS params: CLI flags override everything. If none given, prompt to accept/modify tuned defaults.
    cli_overrides = {
        k: v for k, v in {
            "temperature": args.tts_temp,
            "exaggeration": args.tts_exag,
            "cfg": (args.tts_cfg_weight if args.tts_cfg_weight is not None else args.tts_cfg),
            "cfg_weight": (args.tts_cfg_weight if args.tts_cfg_weight is not None else None),
            "speed": (args.tts_speed_factor if args.tts_speed_factor is not None else args.tts_speed),
            "speed_factor": (args.tts_speed_factor if args.tts_speed_factor is not None else None),
            "seed": args.tts_seed,
        }.items() if v is not None
    }

    def _prompt_tts_params(defaults: dict) -> dict:
        def _get(prompt: str, current: object, cast):
            try:
                s = input(f"{prompt} [{current}]: ").strip()
            except EOFError:
                return current
            if not s:
                return current
            try:
                return cast(s)
            except Exception:
                print("  Invalid input; keeping current.")
                return current
        try:
            use = input(
                (
                    "Use these TTS settings? "
                    f"temp={defaults['temperature']}, exag={defaults['exaggeration']}, cfg={defaults['cfg']}, "
                    f"speed={defaults['speed']}, seed={defaults['seed']} [Y/n] "
                )
            ).strip().lower()
        except EOFError:
            use = "y"
        if use in {"", "y", "yes"}:
            return defaults
        # Allow editing each value
        out = dict(defaults)
        out["temperature"] = _get("Temperature", out["temperature"], float)
        out["exaggeration"] = _get("Exaggeration", out["exaggeration"], float)
        out["cfg"] = _get("CFG weight", out["cfg"], float)
        out["speed"] = _get("Speed factor", out["speed"], float)
        out["seed"] = _get("Seed", out["seed"], int)
        return out

    tts_params: dict
    if cli_overrides:
        tts_params = cli_overrides
    else:
        cfg = TTSConfig()
        if character == "djcara":
            defaults = {
                "temperature": cfg.djcara_temperature if cfg.djcara_temperature is not None else 0.75,
                "exaggeration": cfg.djcara_exaggeration if cfg.djcara_exaggeration is not None else 0.70,
                "cfg": (cfg.djcara_cfg_weight if getattr(cfg, "djcara_cfg_weight", None) is not None else 0.30),
                "speed": cfg.djcara_speed_factor if cfg.djcara_speed_factor is not None else 1.05,
                "seed": (cfg.djcara_seed if getattr(cfg, "djcara_seed", None) is not None else 42),
            }
        else:
            defaults = {
                "temperature": cfg.temperature if cfg.temperature is not None else 0.6,
                "exaggeration": cfg.exaggeration if cfg.exaggeration is not None else 0.9,
                "cfg": cfg.cfg_weight if cfg.cfg_weight is not None else 0.3,
                "speed": cfg.speed_factor if cfg.speed_factor is not None else 1.0,
                "seed": cfg.seed if cfg.seed is not None else 2024,
            }
        chosen = _prompt_tts_params(defaults)
        # The backend accepts either cfg or cfg_weight; include both for clarity.
        tts_params = {
            "temperature": chosen["temperature"],
            "exaggeration": chosen["exaggeration"],
            "cfg": chosen["cfg"],
            "cfg_weight": chosen["cfg"],
            "speed": chosen["speed"],
            "speed_factor": chosen["speed"],
            "seed": chosen["seed"],
        }
    # Generate dialogues (includes metadata and original post)
    dialogues = create_stories(
        subreddit=args.subreddit,
        number_of_posts=1,
        sort=args.sort,
        time_filter=args.time_filter,
        character=character,
        mode=mode,
    )
    # Ensure strictly one post per run
    dialogues = dialogues[:1]

    audio_root = Path(args.output)
    audio_root.mkdir(parents=True, exist_ok=True)

    # Save output JSON for reference (first item only for this CLI)
    dialogues_json = audio_root / "dialogues.json"
    with dialogues_json.open("w", encoding="utf-8") as f:
        json.dump(dialogues, f, indent=2, ensure_ascii=False)

    # Show generated content (first and only item)
    preview = dialogues[0] if dialogues else {}
    if "text" in preview:
        print("\n[2/3] Generated monologue:\n" + "-"*50)
        print(preview["text"][:2000])
        print("\n" + "-"*50)
    elif "lines" in preview:
        print("\n[2/3] Generated story lines:\n" + "-"*50)
        for i, ln in enumerate(preview["lines"], 1):
            print(f"{i:02d}. {ln}")
        print("-"*50)

    # Render combined audio per character for each dialogue
    print("\n[3/3] Synthesizing audio (this may take a moment)...")
    all_outputs = []
    story_title: str | None = None
    for idx, item in enumerate(dialogues, start=1):
        post = item.get("post", {})
        title = post.get("title") or f"dialogue_{idx}"
        story_title = title

        # Single‑speaker monologue
        if "text" in item:
            label = args.default_speaker or (item.get("character") or "dialogue")
            paths = render_single_track_text(
                item["text"],
                title,
                str(audio_root),
                label=label,
                voice_override=args.tts_voice,
                tts_params=tts_params or None,
            )
            print(f"[Done] Monologue audio: {paths[0] if paths else 'n/a'}")
            all_outputs.extend(paths)
            continue

        # Multi‑speaker lines (default)
        lines = item.get("lines", [])
        default_label = args.default_speaker
        final_paths = render_combined_audio(
            lines,
            title,
            str(audio_root),
            default_speaker=default_label,
            single_track=False,
            voice_override=args.tts_voice,
            tts_params=tts_params or None,
        )
        print(f"[Done] Combined audios: {', '.join(final_paths) if final_paths else 'n/a'}")
        all_outputs.extend(final_paths)

    # Optional: intro/outro
    def _ask_yn(prompt: str, default: bool = False) -> bool:
        try:
            ans = input(prompt).strip().lower()
        except EOFError:
            return default
        if not ans:
            return default
        return ans in {"y", "yes"}

    do_intro_outro: bool
    if args.with_intro_outro and args.without_intro_outro:
        do_intro_outro = False
    elif args.with_intro_outro:
        do_intro_outro = True
    elif args.without_intro_outro:
        do_intro_outro = False
    else:
        do_intro_outro = _ask_yn("Add intro/outro from './intro' and './outro'? [y/N] ", default=False)

    if do_intro_outro and all_outputs:
        print("[Intro/Outro] Applying...")
        import os as _os
        # Resolve directories from CLI or env or defaults
        intro_dir = args.intro_dir or _os.getenv("INTRO_DIR")
        outro_dir = args.outro_dir or _os.getenv("OUTRO_DIR")
        iodir = args.intro_outro_dir or _os.getenv("INTRO_OUTRO_DIR")
        # Crossfade default (ms)
        cf_ms = args.crossfade_ms
        if cf_ms is None:
            env_cf = _os.getenv("INTRO_OUTRO_CROSSFADE_MS")
            cf_ms = int(env_cf) if (env_cf and env_cf.isdigit()) else 750
        # Bridge decision
        def _ask_bridge(default: bool) -> bool:
            try:
                ans = input("Generate a short DJ Cara intro line with the story title? [y/N] ").strip().lower()
            except EOFError:
                return default
            if not ans:
                return default
            return ans in {"y", "yes"}
        use_bridge: bool
        if args.with_bridge and args.without_bridge:
            use_bridge = False
        elif args.with_bridge:
            use_bridge = True
        elif args.without_bridge:
            use_bridge = False
        else:
            use_bridge = _ask_bridge(default=(character == "djcara"))

        bridge_text = None
        if use_bridge and character == "djcara":
            # Use a friendly, energetic but clear British DJ Cara line
            st = story_title or (dialogues[0].get("post", {}) or {}).get("title") if dialogues else None
            st = st or "today's story"
            bridge_text = (
                f"Right, it\'s DJ Cara. Today\'s agenda: {st}. Hold tight — let\'s get into it."
            )

        new_paths = apply_intro_outro_to_files(
            all_outputs,
            intro_dir=intro_dir,
            outro_dir=outro_dir,
            intro_outro_dir=iodir,
            crossfade_ms=cf_ms or 0,
            bridge_text=bridge_text,
            voice_override=args.tts_voice,
            tts_params=tts_params or None,
            label=(character if character else None),
        )
        if new_paths:
            print("[Intro/Outro] Completed:")
            for p in new_paths:
                print(f" - {p}")
    print(f"Saved dialogues JSON: {dialogues_json}")

from story_generation.story_generator import create_stories
from content_generation.audio_gen import render_combined_audio, render_single_track_text
from content_generation.tts_backends import get_tts_backend

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
    parser.add_argument("-c", "--character", choices=["rickmorty", "djcara"], default="rickmorty", help="Character style for generation")
    parser.add_argument("--tts-voice", default=None, help="Override TTS voice name for this run (applies to all lines)")
    parser.add_argument("--list-voices", action="store_true", help="List predefined voices from Chatterbox and exit")
    parser.add_argument("--cara", action="store_true", help="Explicitly use Dj Caralong voice (DJ_Caralong.mp3)")
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
        args.tts_voice = "DJ_Caralong.mp3"

    tts_params = {
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
    # Generate dialogues (includes metadata and original post)
    dialogues = create_stories(
        subreddit=args.subreddit,
        number_of_posts=1,
        sort=args.sort,
        time_filter=args.time_filter,
        character=args.character,
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
    for idx, item in enumerate(dialogues, start=1):
        post = item.get("post", {})
        title = post.get("title") or f"dialogue_{idx}"

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

    print(f"Saved dialogues JSON: {dialogues_json}")

# filename: src/beatstoch/cli.py
import argparse
import re
import sys

from .generator import generate_from_song, generate_stochastic_pattern


def main():
    """
    CLI for BPM-aware stochastic drum MIDI generator.
    """
    parser = argparse.ArgumentParser(
        prog="beatstoch",
        description="BPM-aware stochastic drum MIDI generator.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    gsong = sub.add_parser(
        "generate", help="Generate from song title/artist via BPMDatabase."
    )
    gsong.add_argument("title")
    gsong.add_argument("--artist")
    gsong.add_argument("--bars", type=int, default=8)
    gsong.add_argument(
        "--style", default="house", choices=["house", "breaks", "generic"]
    )
    gsong.add_argument("--steps-per-beat", type=int, default=4)
    gsong.add_argument("--swing", type=float, default=0.10)
    gsong.add_argument("--intensity", type=float, default=0.9)
    gsong.add_argument("--groove-intensity", type=float, default=0.7,
                      help="Psychoacoustic groove intensity (0.0-1.0)")
    gsong.add_argument("--seed", type=int)
    gsong.add_argument("--fallback-bpm", type=float)
    gsong.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging for BPM lookup."
    )

    gbpm = sub.add_parser("generate-bpm", help="Generate with explicit BPM.")
    gbpm.add_argument("bpm", type=float)
    gbpm.add_argument("--bars", type=int, default=8)
    gbpm.add_argument(
        "--style", default="house", choices=["house", "breaks", "generic"]
    )
    gbpm.add_argument("--steps-per-beat", type=int, default=4)
    gbpm.add_argument("--swing", type=float, default=0.10)
    gbpm.add_argument("--intensity", type=float, default=0.9)
    gbpm.add_argument("--groove-intensity", type=float, default=0.7,
                      help="Psychoacoustic groove intensity (0.0-1.0)")
    gbpm.add_argument("--seed", type=int)

    args = parser.parse_args()

    if args.cmd == "generate":
        try:
            mid, bpm_used = generate_from_song(
                song_title=args.title,
                artist=args.artist,
                bars=args.bars,
                style=args.style,
                steps_per_beat=args.steps_per_beat,
                swing=args.swing,
                intensity=args.intensity,
                groove_intensity=args.groove_intensity,
                seed=args.seed,
                fallback_bpm=args.fallback_bpm,
                verbose=args.verbose,  # pass through
            )
        except Exception as e:
            print(f"beatstoch: {e}", file=sys.stderr)
            sys.exit(2)

        safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", args.title).strip("_").lower()
        safe_artist = (
            re.sub(r"[^a-zA-Z0-9]+", "_", args.artist).strip("_").lower()
            if args.artist
            else "unknown"
        )
        out_path = f"stoch_{safe_artist}_{safe_title}_{int(bpm_used)}bpm.mid"
        mid.save(out_path)
        print(f"Wrote {out_path} (BPM={bpm_used})")
    else:
        mid = generate_stochastic_pattern(
            bpm=args.bpm,
            bars=args.bars,
            meter=(4, 4),
            steps_per_beat=args.steps_per_beat,
            swing=args.swing,
            intensity=args.intensity,
            groove_intensity=args.groove_intensity,
            seed=args.seed if args.seed is not None else 42,
            style=args.style,
        )
        out_path = f"stoch_{int(args.bpm)}bpm.mid"
        mid.save(out_path)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

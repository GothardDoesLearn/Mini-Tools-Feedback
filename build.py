"""Einstiegspunkt: python build.py [--check | --serve] [--out DIR] [--port N]"""

import argparse
import sys
from pathlib import Path

from generator.build import build
from generator.check import check
from generator.paths import DIST_DIR
from generator.serve import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baut die Feedback-Tools-Website nach dist/.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="nur Inhalte prüfen, nichts bauen")
    mode.add_argument("--serve", action="store_true", help="lokale Vorschau mit Neubau")
    parser.add_argument(
        "--out", type=Path, default=DIST_DIR, help="Ausgabeordner (Standard: dist/)"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port für --serve")
    args = parser.parse_args(argv)

    if args.check:
        check()
        print("Prüfung ok.")
    elif args.serve:
        serve(args.out, rebuild=lambda: build(args.out, check()), port=args.port)
    else:
        build(args.out, check())
        print(f"Gebaut nach {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

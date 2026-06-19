#!/usr/bin/env python3
"""Stack two GIFs vertically (top + bottom) using ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def probe_width(path: Path) -> int:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width",
        "-of",
        "csv=p=0",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Failed to probe: {path}")
    return int(result.stdout.strip())


def stack_gifs(
    top_path: Path,
    bottom_path: Path,
    output_path: Path,
    *,
    width: int | None = None,
    fps: float | None = None,
) -> None:
    if not shutil.which("ffmpeg"):
        sys.exit(
            "ffmpeg not found. Install it first:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg"
        )

    top_path = top_path.resolve()
    bottom_path = bottom_path.resolve()
    output_path = output_path.resolve()

    for path in (top_path, bottom_path):
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    target_width = width if width is not None else probe_width(top_path)

    fps_filter = f",fps={fps}" if fps else ""
    scale = f"scale={target_width}:-1:flags=lanczos"
    stack_filter = (
        f"[0:v]{scale}{fps_filter}[top];"
        f"[1:v]{scale}{fps_filter}[bottom];"
        f"[top][bottom]vstack=inputs=2"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        palette_path = Path(tmp_dir) / "palette.png"

        palette_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(top_path),
            "-i",
            str(bottom_path),
            "-lavfi",
            f"{stack_filter},palettegen=stats_mode=diff",
            str(palette_path),
        ]
        _run(palette_cmd)

        gif_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(top_path),
            "-i",
            str(bottom_path),
            "-i",
            str(palette_path),
            "-lavfi",
            (
                f"{stack_filter}[x];"
                "[x][2:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
            ),
            "-loop",
            "0",
            str(output_path),
        ]
        _run(gif_cmd)


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(stderr or f"Command failed: {' '.join(cmd)}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stack two GIFs vertically (top on top, bottom below)."
    )
    parser.add_argument("top", type=Path, help="Top GIF")
    parser.add_argument("bottom", type=Path, help="Bottom GIF")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output GIF path (default: <top>_stacked.gif)",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Output width in pixels (default: match top GIF width)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        help="Normalize frame rate (default: keep original timing)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output = args.output or args.top.with_name(f"{args.top.stem}_stacked.gif")

    try:
        stack_gifs(
            args.top,
            args.bottom,
            output,
            width=args.width,
            fps=args.fps,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        sys.exit(str(exc))

    print(f"Saved: {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convert MP4 video to animated GIF using ffmpeg palette generation."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def convert(
    input_path: Path,
    output_path: Path,
    *,
    fps: float = 10,
    width: int | None = 480,
    start: str | None = None,
    end: str | None = None,
) -> None:
    if not shutil.which("ffmpeg"):
        sys.exit(
            "ffmpeg not found. Install it first:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg"
        )

    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if width:
        scale = f"scale={width}:-1:flags=lanczos,"
    else:
        scale = ""

    vf_base = f"fps={fps},{scale}".rstrip(",")

    seek_args: list[str] = []
    if start:
        seek_args += ["-ss", start]

    duration_args: list[str] = []
    if end:
        duration_args += ["-to", end]

    with tempfile.TemporaryDirectory() as tmp_dir:
        palette_path = Path(tmp_dir) / "palette.png"

        palette_cmd = [
            "ffmpeg",
            "-y",
            *seek_args,
            "-i",
            str(input_path),
            *duration_args,
            "-vf",
            f"{vf_base},palettegen=stats_mode=diff",
            str(palette_path),
        ]
        _run(palette_cmd)

        gif_cmd = [
            "ffmpeg",
            "-y",
            *seek_args,
            "-i",
            str(input_path),
            *duration_args,
            "-i",
            str(palette_path),
            "-lavfi",
            (
                f"{vf_base}[x];"
                "[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
            ),
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
        description="Convert MP4 to GIF (palette-optimized, smaller file size)."
    )
    parser.add_argument("input", type=Path, help="Input MP4 file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output GIF path (default: same name with .gif extension)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=10,
        help="Output frame rate (default: 10)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=240,
        help="Output width in pixels, height scales automatically (default: 480, use 0 for original)",
    )
    parser.add_argument(
        "--start",
        help="Start time, e.g. 00:00:01 or 1.5",
    )
    parser.add_argument(
        "--end",
        help="End time, e.g. 00:00:05 or 5.0",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output = args.output or args.input.with_suffix(".gif")
    width = None if args.width == 0 else args.width

    try:
        convert(
            args.input,
            output,
            fps=args.fps,
            width=width,
            start=args.start,
            end=args.end,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        sys.exit(str(exc))

    print(f"Saved: {output}")


if __name__ == "__main__":
    main()

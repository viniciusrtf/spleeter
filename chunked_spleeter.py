#!/usr/bin/env python3
"""
chunked_spleeter.py
-------------------
Run Spleeter in memory‑friendly chunks, concatenate the stems, and (optionally)
bootstrap itself inside a given Python virtual‑environment.

NEW FEATURE
===========
--venv / -V : path to a *virtual‑env directory*.  
If supplied and the script is *not already* running inside that venv, it
re‑executes itself with the venv’s Python interpreter, so every subsequent
`ffprobe`, `ffmpeg`, and especially `spleeter` command use the matching venv.

USAGE
=====
# 10‑min chunks, auto‑step into venv at ~/venvs/spleeter
python chunked_spleeter.py original.wav --venv ~/venvs/spleeter

# 5‑min chunks, keep temporary folders
python chunked_spleeter.py original.wav -c 300 --keep-temp
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

################################################################################
# early venv hop‑in
################################################################################
def maybe_reexec_in_venv(venv_dir: Path):
    """If a venv is requested but not active, re‑exec the script inside it."""
    if not venv_dir.exists():
        sys.exit(f"[venv] directory '{venv_dir}' does not exist")

    # Detect venv’s python: POSIX -> bin/python, Windows -> Scripts/python.exe
    venv_python = (
        venv_dir / "bin" / "python"
        if (venv_dir / "bin" / "python").exists()
        else venv_dir / "Scripts" / "python.exe"
    )
    if not venv_python.exists():
        sys.exit(f"[venv] could not find interpreter under {venv_dir}")

    # If we're already inside that venv, VIRTUAL_ENV matches
    if os.environ.get("VIRTUAL_ENV") == str(venv_dir):
        return  # already in

    # Build argv without the --venv flag to avoid recursion
    new_argv = []
    skip_next = False
    for i, token in enumerate(sys.argv):
        if skip_next:
            skip_next = False
            continue
        if token in ("--venv", "-V"):
            # consume next token if it's the path value (not --venv=/path form)
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                skip_next = True
            continue
        elif token.startswith("--venv="):
            continue
        new_argv.append(token)

    print(f"[venv] Relaunching inside {venv_python}")
    cmd = [str(venv_python)] + new_argv
    os.execv(str(venv_python), cmd)


################################################################################
# shell helpers
################################################################################
def run(cmd, **popen_kwargs):
    """Run *cmd* list and raise if non‑zero exit."""
    print("»", " ".join(map(str, cmd)))
    proc = subprocess.run(cmd, **popen_kwargs)
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return proc


def get_duration_sec(audio_path: Path) -> float:
    """Retrieve duration with ffprobe (seconds, float)."""
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio_path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def ffmpeg_concat(wav_list, output_path):
    """Concatenate WAVs losslessly via FFmpeg concat demuxer."""
    concat_file = output_path.with_suffix(".txt")
    with concat_file.open("w") as f:
        for w in wav_list:
            f.write(f"file '{w.as_posix()}'\n")

    try:
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]
        )
    finally:
        concat_file.unlink(missing_ok=True)


################################################################################
# main
################################################################################
def main():
    p = argparse.ArgumentParser(
        description="Chunked Spleeter wrapper (with optional venv activation)."
    )
    p.add_argument("input", type=Path, help="Input audio file")
    p.add_argument(
        "-c",
        "--chunk",
        type=int,
        default=600,
        help="Chunk size in seconds (default 600)",
    )
    p.add_argument(
        "--model",
        default="spleeter:2stems",
        help='Spleeter model (default "spleeter:2stems")',
    )
    p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Final output directory",
    )
    p.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep per‑chunk temp directories",
    )
    p.add_argument(
        "-V",
        "--venv",
        type=Path,
        help="Path to virtual‑environment directory to activate first",
    )
    args = p.parse_args()

    # ——— hop into venv early if requested ———
    if args.venv:
        maybe_reexec_in_venv(args.venv)

    in_path = args.input.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        sys.exit(f"Input file '{in_path}' not found")

    total_sec = get_duration_sec(in_path)
    n_chunks = math.ceil(total_sec / args.chunk)
    print(f"Duration {total_sec:.2f}s → {n_chunks} chunk(s) of {args.chunk}s")

    with tempfile.TemporaryDirectory(prefix="spleeter_chunk_") as tmp_root:
        tmp_root = Path(tmp_root)
        vocal_parts = []
        accomp_parts = []

        for idx in range(n_chunks):
            offset = idx * args.chunk
            chunk_dir = tmp_root / f"chunk{idx}"
            stem_dir = chunk_dir / in_path.stem
            chunk_dir.mkdir(parents=True)

            spleeter_cmd = [
                sys.executable,  # venv's interpreter
                "-m", "spleeter", "separate",
                "-p", args.model,
                "--offset", str(offset),
                "-d",       str(args.chunk),
                "-o",       str(chunk_dir),
                str(in_path),
            ]
            run(spleeter_cmd)

            vocal_file = stem_dir / "vocals.wav"
            accomp_file = stem_dir / "accompaniment.wav"
            if not vocal_file.exists():
                sys.exit(f"Missing {vocal_file}")
            vocal_parts.append(vocal_file)
            accomp_parts.append(accomp_file)

        # concatenate
        final_vocals = out_dir / f"{in_path.stem}_vocals.wav"
        final_accomp = out_dir / f"{in_path.stem}_accompaniment.wav"
        print("► Concatenating vocals …")
        ffmpeg_concat(vocal_parts, final_vocals)
        print("► Concatenating accompaniment …")
        ffmpeg_concat(accomp_parts, final_accomp)

        if args.keep_temp:
            print(f"[temp] chunks kept under {tmp_root}")

    print("\n✔ Finished")
    print(f" • {final_vocals}")
    print(f" • {final_accomp}")


if __name__ == "__main__":
    main()


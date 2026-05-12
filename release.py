#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import zipfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SOUNDS_DIR = SCRIPT_DIR / "SOUNDS"
RELEASE_DIR = SCRIPT_DIR / "release"
console = Console()


def env_flags(name: str, default: str) -> list[str]:
    return shlex.split(os.environ.get(name, default))


def recreate_release_dir() -> None:
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir()


def create_release_directories() -> None:
    for source_dir in SOUNDS_DIR.rglob("*"):
        if source_dir.is_dir():
            (RELEASE_DIR / source_dir.relative_to(SCRIPT_DIR)).mkdir(parents=True, exist_ok=True)


def process_audio_files(ffmpeg_flags: list[str], ffmpeg_af_flags: str) -> int:
    sound_files = sorted(SOUNDS_DIR.rglob("*.wav"))
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Processing audio", total=len(sound_files))
        for source_file in sound_files:
            progress.update(task_id, description=f"Processing {source_file.relative_to(SCRIPT_DIR)}")
            output_file = RELEASE_DIR / source_file.relative_to(SOUNDS_DIR.parent)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            subprocess.run(
                [
                    "ffmpeg",
                    *ffmpeg_flags,
                    "-i",
                    str(source_file),
                    "-af",
                    ffmpeg_af_flags,
                    str(output_file),
                ],
                check=True,
                cwd=SCRIPT_DIR,
            )
            subprocess.run(
                [
                    "uv",
                    "run",
                    "ffmpeg-normalize",
                    str(output_file),
                    "-o",
                    str(output_file),
                    "-f",
                    "-nt",
                    "peak",
                    "-t",
                    "0",
                ],
                check=True,
                cwd=SCRIPT_DIR,
            )
            progress.advance(task_id)

    return len(sound_files)


def move_variant_directories() -> None:
    root_sounds_dir = RELEASE_DIR / "SOUNDS"
    for variant_dir in sorted(root_sounds_dir.iterdir()):
        if not variant_dir.is_dir():
            continue
        destination = RELEASE_DIR / variant_dir.name / "SOUNDS"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(variant_dir), str(destination))


def trim_variant_directories() -> None:
    for variant_dir in sorted(RELEASE_DIR.iterdir()):
        if not variant_dir.is_dir() or variant_dir.name == "SOUNDS":
            continue
        current_lang_dir = variant_dir / "SOUNDS" / variant_dir.name
        target_lang_dir = variant_dir / "SOUNDS" / variant_dir.name[:2]
        if current_lang_dir.exists() and current_lang_dir != target_lang_dir:
            console.print(f"[cyan]{variant_dir.name} -> {target_lang_dir.name}[/cyan]")
            current_lang_dir.rename(target_lang_dir)


def remove_root_sounds_dir() -> None:
    root_sounds_dir = RELEASE_DIR / "SOUNDS"
    if root_sounds_dir.exists():
        root_sounds_dir.rmdir()


def create_release_archives(version: str) -> int:
    variant_dirs = sorted(path for path in RELEASE_DIR.iterdir() if path.is_dir())
    archive_count = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Creating archives", total=len(variant_dirs))
        for variant_dir in variant_dirs:
            sounds_root = variant_dir / "SOUNDS"
            if not sounds_root.is_dir():
                progress.advance(task_id)
                continue

            progress.update(task_id, description=f"Zipping {variant_dir.name}")
            archive_path = RELEASE_DIR / f"edgetx-sdcard-sounds-{variant_dir.name}-{version}.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for file_path in sorted(sounds_root.rglob("*")):
                    if file_path.is_file():
                        archive.write(file_path, arcname=file_path.relative_to(variant_dir))
            archive_count += 1
            progress.advance(task_id)

    return archive_count


def main() -> int:
    os.chdir(SCRIPT_DIR)

    version = os.environ.get("VERSION", "latest")
    ffmpeg_flags = env_flags("FFMPEG_FLAGS", "-hide_banner -loglevel error")
    ffmpeg_af_flags = os.environ.get(
        "FFMPEG_AF_FLAGS",
        "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,"
        "areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse",
    )

    recreate_release_dir()

    console.print(
        Panel.fit(
            f"VERSION         : {version}\n"
            f"FFMPEG_FLAGS    : {' '.join(ffmpeg_flags)}\n"
            f"FFMPEG_AF_FLAGS : {ffmpeg_af_flags}",
            title="release.py",
        )
    )
    console.print("Creating release folders...")
    create_release_directories()
    processed_count = process_audio_files(ffmpeg_flags, ffmpeg_af_flags)
    move_variant_directories()
    trim_variant_directories()
    remove_root_sounds_dir()
    archive_count = create_release_archives(version)

    console.print(
        f"[green]Processed {processed_count} audio file(s) and created {archive_count} archive(s).[/green]"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Command failed with exit code {exc.returncode}.[/red]")
        raise SystemExit(exc.returncode) from exc
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc

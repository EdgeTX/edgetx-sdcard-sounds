#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
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

from voice_generation_config import AZURE_VOICE_JOBS, GLADOS_VOICE_JOBS


SCRIPT_DIR = Path(__file__).resolve().parent
console = Console()


def run_checked(command: list[str], *, quiet: bool = False) -> None:
    kwargs: dict[str, object] = {"cwd": SCRIPT_DIR}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    completed = subprocess.run(command, check=False, **kwargs)
    if completed.returncode in (130, -2):
        raise KeyboardInterrupt
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)


def ensure_file_exists(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")


def ensure_ffmpeg_normalize_available() -> None:
    if shutil.which("ffmpeg-normalize"):
        return

    try:
        subprocess.run(
            ["uv", "run", "--quiet", "ffmpeg-normalize", "--version"],
            check=True,
            cwd=SCRIPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("ffmpeg-normalize not found in PATH or uv environment.") from exc


def remove_previous_logs() -> int:
    removed = 0
    for log_file in SCRIPT_DIR.rglob("*.log"):
        log_file.unlink()
        removed += 1
    return removed


def run_command(command: list[str], label: str, progress: Progress | None = None) -> None:
    console.print(f"[cyan]{label}[/cyan]")
    if progress is not None:
        progress.stop()
    try:
        run_checked(command)
    finally:
        if progress is not None:
            progress.start()


def build_azure_command(csv_file: str, voice: str, langdir: str, pitch: str | None, rate: str | None) -> list[str]:
    command = ["uv", "run", "./voice-gen-azure.py", csv_file, voice, langdir]
    if pitch:
        command.extend(["--pitch", pitch])
    if rate:
        command.extend(["--rate", rate])
    return command


def main() -> int:
    os.chdir(SCRIPT_DIR)

    ensure_ffmpeg_normalize_available()
    ensure_file_exists(SCRIPT_DIR / "voice-gen-azure.py")
    ensure_file_exists(SCRIPT_DIR / "voice-gen-glados.py")
    ensure_file_exists(SCRIPT_DIR / "voice-gen-elevenlabs.py")

    removed_logs = remove_previous_logs()
    console.print(
        Panel.fit(
            f"Generating EdgeTX sound packs\nRemoved {removed_logs} stale log file(s)",
            title="generate.py",
        )
    )

    total_jobs = len(AZURE_VOICE_JOBS) + len(GLADOS_VOICE_JOBS) + 1
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Azure voices", total=total_jobs)

        for job in AZURE_VOICE_JOBS:
            progress.update(task_id, description=f"Azure: {job.langdir}")
            run_command(
                build_azure_command(job.csv_file, job.voice, job.langdir, job.pitch, job.rate),
                f"Azure {job.langdir}: {job.csv_file} -> {job.voice}",
                progress,
            )
            progress.advance(task_id)

        for job in GLADOS_VOICE_JOBS:
            progress.update(task_id, description=f"GLaDOS: {job.langdir}")
            run_command(
                ["uv", "run", "./voice-gen-glados.py", job.csv_file, job.langdir],
                f"GLaDOS {job.langdir}: {job.csv_file}",
                progress,
            )
            progress.advance(task_id)

        progress.update(task_id, description="ElevenLabs")
        run_command(["uv", "run", "./voice-gen-elevenlabs.py"], "ElevenLabs", progress)
        progress.advance(task_id)

    console.print("[green]Generation completed.[/green]")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user (Ctrl+C).[/yellow]")
        raise SystemExit(130)
    except subprocess.CalledProcessError as exc:
        if exc.returncode in (130, -2):
            console.print("[yellow]Interrupted by user (Ctrl+C).[/yellow]")
            raise SystemExit(130) from exc
        console.print(f"[red]Command failed with exit code {exc.returncode}.[/red]")
        raise SystemExit(exc.returncode) from exc
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc

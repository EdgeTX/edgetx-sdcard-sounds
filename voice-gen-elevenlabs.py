#!/usr/bin/env python3
import csv
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

load_dotenv()

# Getting API key from environment variable
# set the variable by:
# export ELEVENLABS_API_KEY="<Api key>"
api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    raise RuntimeError(
        'Environment variable ELEVENLABS_API_KEY not set. Use command:\nexport ELEVENLABS_API_KEY="<Api key>"'
    )

# Init ElevenLabs
client = ElevenLabs(api_key=api_key)

# Array of languages
# file, voice ID, language subdir
languages = [
    ("voices/pl-PL.csv", "EXAVITQu4vr4xnSDxMaL", "pl"),
    # Add other languages here
]

in_ci = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
total_files = len(languages)


def process_csv_file(
    csv_file: str,
    voice_name: str,
    output_dir: str,
    processed_files: int,
    total_files: int,
) -> None:
    """Process a single CSV file."""
    console = Console(force_terminal=not in_ci, no_color=in_ci)
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        TextColumn("{task.fields[status]}", justify="left"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
        expand=True,
    )

    class StatusLine:
        def __init__(self) -> None:
            self.message = ""

        def update(self, message: str) -> None:
            self.message = message

        def __rich_console__(self, console, options):
            yield Text(self.message)

    status_line = StatusLine()
    layout = Group(status_line, progress)

    print(f"\nProcessing file {csv_file}")

    csv_path = Path(csv_file)
    with csv_path.open(newline="", encoding="utf-8") as f, Live(
        layout, console=console, refresh_per_second=10, transient=False
    ):
        reader = csv.DictReader(f)
        rows = list(reader)
        total_rows = len(rows)
        task_id = progress.add_task("Synthesizing", total=total_rows or None, status="")

        def report(msg: str) -> None:
            if in_ci:
                progress.console.print(msg)
            else:
                status_line.update(msg)
                progress.refresh()

        processed_count = 0
        line_count = 0

        try:
            fail_streak = 0
            for row in rows:
                line_count += 1
                try:
                    if not row.get("Filename") or row.get("String ID", "").startswith(
                        "#"
                    ):
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        continue

                    name = Path(row["Filename"]).stem
                    tr = row.get("Translation", "")
                    subd = row.get("Path", "")
                    skip = row.get("Skip") or "0.0"

                    full_dir = Path("SOUNDS") / output_dir / subd
                    full_dir.mkdir(parents=True, exist_ok=True)
                    output_mp3 = full_dir / f"{name}.mp3"
                    output_wav = full_dir / f"{name}.wav"

                    # To save free tokens available on Elevenlabs - skip existing files to avoid double generating
                    if output_wav.exists():
                        report(
                            f'[{line_count}/{total_rows}] Skipping "{name}.wav" as already exists.'
                        )
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        fail_streak = 0
                        continue

                    report(
                        f"[{line_count}/{total_rows}] Generating MP3 file: {output_mp3} ..."
                    )

                    audio_generator = client.text_to_speech.convert(
                        text=tr,
                        voice_id=voice_name,
                        model_id="eleven_multilingual_v2",
                        output_format="mp3_44100_128",
                    )

                    audio_bytes = b"".join(audio_generator)
                    output_mp3.write_bytes(audio_bytes)

                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-ss",
                        skip,
                        "-y",
                        "-i",
                        str(output_mp3),
                        "-ar",
                        "32000",
                        "-ac",
                        "1",
                        "-sample_fmt",
                        "s16",
                        str(output_wav),
                    ]

                    subprocess.run(ffmpeg_cmd, check=True)

                    # Remove temporary mp3 file
                    if output_mp3.exists():
                        output_mp3.unlink()

                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak = 0
                except Exception as e:
                    report(f"[{line_count}/{total_rows}] Error processing row: {e}")
                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak += 1
                    if fail_streak >= 3:
                        report("Aborting after 3 consecutive failures")
                        raise SystemExit(1)
                    continue
        except KeyboardInterrupt:
            report(
                f"Interrupted. Processed {processed_files}/{total_files} files; {processed_count}/{total_rows} entries in current file."
            )
            progress.update(task_id, completed=processed_count)
            raise SystemExit(1)

        report(
            f'Finished processing {processed_files}/{total_files} files ({processed_count}/{total_rows} entries) in "{csv_file}".'
        )


for idx, (csv_file, voice_name, output_dir) in enumerate(languages, 1):
    try:
        process_csv_file(csv_file, voice_name, output_dir, idx, total_files)
    except SystemExit as e:
        if e.code == 1:
            print("\nProcessing interrupted by user.")
            sys.exit(1)
        raise

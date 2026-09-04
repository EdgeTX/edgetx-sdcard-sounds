#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "python-dotenv",
#     "rich",
# ]
# ///
"""
Fourth experimental alternative to voice-gen-glados.py, for comparison
against voice-gen-glados-local.py, voice-gen-glados-rvc.py and
voice-gen-glados-sbv2.py.

The other three scripts run a model locally. This one instead calls the
hosted Fish Audio TTS API (https://fish.audio/) with a community-trained
GLaDOS voice model, model id ee885900b0874d12b1c3439d1e56cc95:

  https://fish.audio/m/ee885900b0874d12b1c3439d1e56cc95/

No local model/GPU/dependency wrangling needed - just an API key - but it's
a paid, rate-limited third-party service rather than something we control,
same tradeoff the original hosted glados.c-net.org endpoint had.

Not wired into generate.py - run standalone and compare output quality and
cost against the other voice-gen-glados-*.py scripts.

One-time setup:

  1. Create an API key at https://fish.audio/app/api-keys/
  2. Set it in the environment, e.g. in a .env file in the repo root:

       FISHAUDIO_API_KEY=your-key-here

Usage (from the repo root, via `uv run`, which picks up this script's own
inline dependencies above):

  uv run ./voice-gen-glados-fishaudio.py voices/en-GB.csv en_gb-glados-fishaudio
"""
import argparse
import csv
import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv
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

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_ID = "ee885900b0874d12b1c3439d1e56cc95"
API_URL = "https://api.fish.audio/v1/tts"


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [FILE] [LANGDIR] [--model-id ID]",
        description="Generate voice packs from CSV list using the Fish Audio TTS API "
        "(https://fish.audio/) with a GLaDOS voice model.",
    )

    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} version 0.1.0")

    parser.add_argument("file", type=str, help="CSV Translation file")

    parser.add_argument("langdir", type=str, help="Language subfolder")

    parser.add_argument(
        "--model-id",
        type=str,
        default=DEFAULT_MODEL_ID,
        help=f"Fish Audio voice/reference_id to use (default: {DEFAULT_MODEL_ID}, the GLaDOS voice)",
    )

    parser.add_argument(
        "--engine-model",
        type=str,
        default=None,
        help="Fish Audio TTS engine tier, sent as the 'model' header (e.g. s2.1-pro, s2.1-pro-free). "
        "Default: omit, let the API use its own default.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Expressiveness/variation, 0.0-1.0 (default: 0.7)",
    )

    return parser


def synthesize(api_key: str, model_id: str, engine_model: str | None, text: str, temperature: float) -> bytes:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if engine_model:
        headers["model"] = engine_model

    # A lot of our phrases have no trailing punctuation (e.g. "wings folded").
    # Without a clear end-of-sentence cue, generative TTS models can cut off
    # abruptly instead of closing out naturally - so force one, same trick
    # glados-tts's own prepare_text() uses. Skip bare numbers though (e.g. the
    # SYSTEM CSV's "4", "200", ...) - a trailing "." there risks being read as a
    # decimal point instead of a sentence end.
    if text and text[-1] not in ".?!" and any(c.isalpha() for c in text):
        text = text + "."

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "text": text,
            "reference_id": model_id,
            "format": "wav",
            "temperature": temperature,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.content


def process_sample(infile: str, outfile: str):
    os.system(f'ffmpeg -loglevel warning -i "{infile}" -ar 32000 "{outfile}"')


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("FISHAUDIO_API_KEY")
    if not api_key:
        raise SystemExit(
            "Environment variable FISHAUDIO_API_KEY not set. Create a key at "
            "https://fish.audio/app/api-keys/ and set it, e.g. in a .env file:\n"
            "  FISHAUDIO_API_KEY=your-key-here"
        )

    print(f"Running {os.path.basename(__file__)} to process file: {args.file}")

    csv_file = args.file
    langdir = args.langdir
    basedir = SCRIPT_DIR
    outdir = Path()

    in_ci = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"

    if not os.path.isfile(csv_file):
        print("Error: voice file not found")
        sys.exit(1)

    csv_path = Path(csv_file).resolve()

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

    with csv_path.open(newline="", encoding="utf-8") as csvfile, Live(
        layout, console=console, refresh_per_second=10, transient=False
    ):
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        total_rows = len(rows)
        task_id = progress.add_task("Synthesizing", total=total_rows or None, status="")

        def report(msg: str) -> None:
            if in_ci:
                progress.console.print(msg)
            else:
                status_line.update(msg)
                progress.refresh()

        line_count = 0
        processed_count = 0

        try:
            fail_streak = 0
            for row in rows:
                line_count += 1
                try:
                    en_text = row.get("Source text", "")
                    text = row.get("Translation", "")
                    path_part = row.get("Path", "")
                    filename = row.get("Filename", "")

                    outdir = basedir / "SOUNDS" / langdir / path_part if path_part else basedir / "SOUNDS" / langdir
                    outfile = outdir / filename if filename else None

                    if not filename:
                        report(f"[{line_count}/{total_rows}] Skipping row with no filename")
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        continue

                    outdir.mkdir(parents=True, exist_ok=True)

                    if not text:
                        report(f"[{line_count}/{total_rows}] Skipping as no text to translate")
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        continue

                    if not outfile.exists():
                        report(f'[{line_count}/{total_rows}] Translate "{en_text}" to "{text}", save as "{outfile}".')

                        audio_bytes = synthesize(api_key, args.model_id, args.engine_model, text, args.temperature)
                        tmpfile_fd, tmpfile = tempfile.mkstemp(suffix=".wav")
                        os.close(tmpfile_fd)
                        try:
                            Path(tmpfile).write_bytes(audio_bytes)
                            process_sample(tmpfile, str(outfile))
                        finally:
                            os.unlink(tmpfile)

                    else:
                        report(f'[{line_count}/{total_rows}] Skipping "{filename}" as already exists.')

                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak = 0
                except Exception as e:
                    progress.console.print_exception(show_locals=False)
                    report(f"[{line_count}/{total_rows}] Error processing row: {e}")
                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak += 1
                    if fail_streak >= 3:
                        report("Aborting after 3 consecutive failures")
                        raise SystemExit(1)
                    continue
        except KeyboardInterrupt:
            report(f"Interrupted. {processed_count}/{total_rows} entries processed.")
            progress.update(task_id, completed=processed_count)
            raise SystemExit(1)

        report(
            f'Finished processing ({processed_count}/{total_rows} entries) from "{csv_file}" '
            f"using {os.path.basename(__file__)}."
        )


if __name__ == "__main__":
    main()

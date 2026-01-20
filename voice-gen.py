#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from rich.console import Console
from rich.console import Group
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

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""
    Importing the Speech SDK for Python failed.
    Refer to
    https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech for
    installation instructions.
    """)
    sys.exit(1)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [FILE] [VOICE] [LANGDIR] [-l LOCALE] [-p PITCH] [-r RATE] [-s DELAY]",
        description="Generate voice packs from CSV list.",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"{parser.prog} version 1.0.0"
    )

    parser.add_argument("file", type=str, help="CSV Translation file")

    parser.add_argument("voice", type=str, help="Voice to use")

    parser.add_argument(
        "-l",
        "--locale",
        type=str,
        help="Language locale",
        required=False,
    )

    parser.add_argument("langdir", type=str, help="Language subfolder")

    parser.add_argument(
        "-p",
        "--pitch",
        help="Pitch adjustment (e.g., 'up10%', 'dn5%', '0.9', '1.25')",
        type=str,
        default="default",
    )

    parser.add_argument(
        "-r",
        "--rate",
        help="Rate adjustment (e.g., 'up10%', 'dn5%')",
        type=str,
        default="default",
    )

    parser.add_argument(
        "-s",
        "--delay",
        type=int,
        help="Sleep time (in seconds) between processing each translation",
        required=False,
        default=3,
    )

    return parser


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    load_dotenv()

    # Print which script is running and the file being processed
    print(f"Running {os.path.basename(__file__)} to process file: {args.file}")

    csv_file = args.file
    csv_rows = 0
    voice = args.voice
    langdir = args.langdir
    basedir = Path(__file__).resolve().parent
    outdir = Path()
    pitch = args.pitch
    rate = args.rate
    delay_time = args.delay

    if args.locale is not None:
        locale = args.locale
    else:
        locale = re.split("([a-z]{2}-[A-Z]{2})", voice)[1]

    if pitch != "default":
        pitch = pitch.replace("dn", "-").replace("up", "+")

    if rate != "default":
        rate = rate.replace("dn", "-").replace("up", "+")

    speech_key = os.environ.get("COGNITIVE_SERVICE_API_KEY")
    service_region = os.environ.get("SERVICE_REGION")

    if not speech_key or not service_region:
        print(
            "ERROR: Please set COGNITIVE_SERVICE_API_KEY and SERVICE_REGION (env or .env file)."
        )
        sys.exit(1)

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region
    )

    if not os.path.isfile(csv_file):
        print("Error: voice file not found")
        sys.exit(1)

    # Get number of rows in CSV file
    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        reader = ((field.strip() for field in row) for row in reader)  # Strip spaces
        csv_rows = sum(1 for row in reader)

    # Drop header row from progress count if present
    csv_rows = max(csv_rows - 1, 0)

    in_ci = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"

    csv_path = Path(csv_file).resolve()
    voices_root = Path(__file__).resolve().parent / "voices"

    all_csvs = sorted(voices_root.glob("*.csv")) if voices_root.exists() else []
    if not all_csvs:
        all_csvs = sorted(csv_path.parent.glob("*.csv"))

    total_files = len(all_csvs) if all_csvs else 1
    processed_files = next(
        (idx + 1 for idx, f in enumerate(all_csvs) if f.resolve() == csv_path), 1
    )

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

    # Process CSV file with progress bar
    with open(csv_file, "rt") as csvfile, Live(
        layout, console=console, refresh_per_second=10, transient=False
    ):
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        reader = ((field.strip() for field in row) for row in reader)  # Strip spaces
        task_id = progress.add_task("Synthesizing", total=csv_rows or None, status="")

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
            for row in reader:
                row = list(row)  # Convert the generator to a list
                line_count += 1
                if line_count == 1:
                    # absorb header row
                    continue

                try:
                    path_part = row[4] if len(row) > 4 else ""
                    outdir = (
                        basedir / "SOUNDS" / langdir / path_part
                        if path_part
                        else basedir / "SOUNDS" / langdir
                    )
                    en_text = row[1] if len(row) > 1 else ""
                    text = row[2] if len(row) > 2 else ""
                    filename = row[5] if len(row) > 5 else ""

                    if not filename:
                        report(
                            f"[{line_count}/{csv_rows}] Skipping row with no filename"
                        )
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        continue

                    outfile = outdir / filename

                    outdir.mkdir(parents=True, exist_ok=True)

                    if not text:
                        report(
                            f"[{line_count}/{csv_rows}] Skipping as no text to translate"
                        )
                        progress.update(task_id, advance=1)
                        processed_count += 1
                        continue

                    if not outfile.exists():
                        report(
                            f'[{line_count}/{csv_rows}] Translate "{en_text}" to "{text}", save as "{outfile}".'
                        )
                        audio_config = speechsdk.audio.AudioOutputConfig(
                            filename=str(outfile)
                        )
                        synthesizer = speechsdk.SpeechSynthesizer(
                            speech_config=speech_config, audio_config=audio_config
                        )

                        ssml_text = f"""
                            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{locale}">
                                <voice name="{voice}">
                                    <prosody pitch="{pitch}" rate="{rate}">{text}</prosody>
                                </voice>
                            </speak>"""

                        result = synthesizer.speak_ssml_async(ssml=ssml_text).get()

                        # If failed, show error, remove empty/corrupt file and count a failure
                        if result.reason == speechsdk.ResultReason.Canceled:
                            cancellation_details = result.cancellation_details
                            report(
                                f"Speech synthesis canceled: {cancellation_details.reason}"
                            )
                            if (
                                cancellation_details.reason
                                == speechsdk.CancellationReason.Error
                            ):
                                report(
                                    f"Error details: {cancellation_details.error_details}"
                                )
                            if outfile.exists():
                                outfile.unlink()
                            fail_streak += 1
                            if fail_streak >= 3:
                                report("Aborting after 3 consecutive failures")
                                raise SystemExit(1)
                            continue

                        time.sleep(delay_time)

                    else:
                        report(
                            f'[{line_count}/{csv_rows}] Skipping "{filename}" as already exists.'
                        )

                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak = 0

                except Exception as e:
                    report(f"[{line_count}/{csv_rows}] Error processing row: {e}")
                    progress.update(task_id, advance=1)
                    processed_count += 1
                    fail_streak += 1
                    if fail_streak >= 3:
                        report("Aborting after 3 consecutive failures")
                        raise SystemExit(1)
                    continue

        except KeyboardInterrupt:
            report(
                f"Interrupted. Processed {processed_files}/{total_files} files; {processed_count}/{csv_rows} entries in current file."
            )
            progress.update(task_id, completed=processed_count)
            raise SystemExit(1)

        report(
            f'Finished processing {processed_files}/{total_files} files ({processed_count}/{csv_rows} entries) from "{csv_file}" using {os.path.basename(__file__)}.'
        )


if __name__ == "__main__":
    main()

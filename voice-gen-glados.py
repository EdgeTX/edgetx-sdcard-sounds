#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

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


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [FILE] [LANGDIR] [-s DELAY]",
        description="Generate voice packs from CSV list using https://glados.c-net.org/"
    )

    parser.add_argument(
        "-v", "--version", action="version",
        version=f"{parser.prog} version 1.0.0"
    )

    parser.add_argument('file',
                        type=str,
                        help="CSV Translation file"
                        )

    parser.add_argument('langdir',
                        type=str,
                        help="Language subfolder"
                        )

    parser.add_argument('-s',
                        '--delay',
                        type=int,
                        help="Sleep time (in seconds) between processing each translation",
                        required=False,
                        default=3
                        )

    return parser

def try_fetch_sample(req: urllib.request.Request, outfile_fd):
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            content = response.read()

            if content[0:4] == b'RIFF' and content[8:12] == b'WAVE':
                with os.fdopen(outfile_fd, 'wb') as out:
                    out.write(content)
                return
            else:
                raise ValueError("Content returned isn't a WAV file!")
        raise ValueError(f"Speech synthesis failed with status code: {response.status}")

def fetch_sample(text: str, outfile_fd, delay_time: int):
    query = urllib.parse.urlencode({"text": text})
    req = urllib.request.Request(f"https://glados.c-net.org/generate?{query}")

    attempts = 50
    for i in range(0, attempts):
        try:
            try_fetch_sample(req, outfile_fd)
            return
        except Exception as e:
            if i == attempts - 1:
                raise e
        finally:
            time.sleep(delay_time)

def process_sample(infile: str, outfile: str):
    os.system(f'ffmpeg -loglevel warning -i {infile} -ar 32000 {outfile}')

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    # Print which script is running and the file being processed
    print(f"Running {os.path.basename(__file__)} to process file: {args.file}")

    csv_file = args.file
    csv_rows = 0
    langdir = args.langdir
    basedir = os.path.dirname(os.path.abspath(__file__))
    outdir = ""
    delay_time = args.delay

    in_ci = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"

    csv_path = Path(csv_file).resolve()
    voices_root = Path(__file__).resolve().parent / "voices"

    all_csvs = sorted(voices_root.glob("*.csv")) if voices_root.exists() else []
    if not all_csvs:
        all_csvs = sorted(csv_path.parent.glob("*.csv"))

    total_files = len(all_csvs) if all_csvs else 1
    processed_files = next((idx + 1 for idx, f in enumerate(all_csvs) if f.resolve() == csv_path), 1)

    if not os.path.isfile(csv_file):
        print("Error: voice file not found")
        sys.exit(1)

    # Get number of rows in CSV file
    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        reader = ((field.strip().strip('"') for field in row) for row in reader)  # Strip spaces and quotes
        csv_rows = sum(1 for row in reader)

    # Drop header row from progress count if present
    csv_rows = max(csv_rows - 1, 0)

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
    with open(csv_file, 'rt') as csvfile, Live(layout, console=console, refresh_per_second=10, transient=False):
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader = ((field.strip().strip('"') for field in row) for row in reader)  # Strip spaces and quotes
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
            for row in reader:
                row = list(row)  # Convert the generator to a list
                if line_count == 0:
                    # absorb header row
                    line_count += 1
                    continue
                if row[4] is None or row[4] == "":
                    outdir = os.path.join(basedir, "SOUNDS", langdir)
                else:
                    outdir = os.path.join(basedir, "SOUNDS", langdir, row[4])
                en_text = row[1]
                text = row[2]
                filename = row[5]
                outfile = os.path.join(outdir, filename)

                tmpfile_fd, tmpfile = tempfile.mkstemp()

                if not os.path.exists(outdir):
                    os.makedirs(outdir)

                if text is None or text == "":
                    report(
                        f'[{line_count}/{csv_rows}] Skipping as no text to translate')
                    progress.update(task_id, advance=1)
                    processed_count += 1
                    line_count += 1
                    continue

                if not os.path.isfile(outfile):
                    report(
                        f'[{line_count}/{csv_rows}] Translate "{en_text}" to "{text}", save as "{outdir}{os.sep}{filename}".')

                    fetch_sample(text, tmpfile_fd, delay_time)
                    process_sample(tmpfile, outfile)
                    os.unlink(tmpfile)

                else:
                    report(
                        f'[{line_count}/{csv_rows}] Skipping "{filename}" as already exists.')

                progress.update(task_id, advance=1)
                processed_count += 1
                line_count += 1
        except KeyboardInterrupt:
            report(
                f"Interrupted. Processed {processed_files}/{total_files} files; {processed_count}/{csv_rows} entries in current file."
            )
            progress.update(task_id, completed=processed_count)
            raise SystemExit(1)

        report(
            f'Finished processing {processed_files}/{total_files} files ({processed_count}/{csv_rows} entries) from "{csv_file}" using {os.path.basename(__file__)}.')


if __name__ == "__main__":
    main()

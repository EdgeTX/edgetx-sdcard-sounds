#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
import urllib.request
import urllib.parse
import tempfile

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [FILE] [LANGDIR]",
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
                        help="Sleep time processing each translation",
                        required=False,
                        default='3'
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
                raise ValueError(f"Content returned isn't a WAV file")
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
    os.system(f'ffmpeg -i {infile} -ar 32000 {outfile}')

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    csv_file = args.file
    csv_rows = 0
    langdir = args.langdir
    basedir = os.path.dirname(os.path.abspath(__file__))
    outdir = ""
    delay_time = args.delay

    if not os.path.isfile(csv_file):
        print("Error: voice file not found")
        sys.exit(1)

    # Get number of rows in CSV file
    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        csv_rows = sum(1 for row in reader)

    # Process CSV file
    with open(csv_file, 'rt') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        line_count = 0
        for row in reader:
            if line_count == 0:
                # print(f'Column names are {", ".join(row)}')
                line_count += 1
                csv_rows -= 1
            else:
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
                    print(
                        f'[{line_count}/{csv_rows}] Skipping as no text to translate')
                    continue

                if not os.path.isfile(outfile):
                    print(
                        f'[{line_count}/{csv_rows}] Translate "{en_text}" to "{text}", save as "{outdir}{os.sep}{filename}".')

                    fetch_sample(text, tmpfile_fd, delay_time)
                    process_sample(tmpfile, outfile)
                    os.unlink(tmpfile)

                else:
                    print(
                        f'[{line_count}/{csv_rows}] Skipping "{filename}" as already exists.')

                line_count += 1

        print(f'Finished processing {csv_rows} entries from "{csv_file}".')


if __name__ == "__main__":
    main()

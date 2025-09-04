#!/usr/bin/env python3
from typing import Iterator, List
from pathlib import Path

import csv
import json
import sys
import logging


EX_OK = 0
EX_DATAERR = 65

csv_directory: Path = Path("voices")
sound_directory: Path = Path("SOUNDS")
IGNORE_FILE: str = ".skip_checkFilesInSoundsNotInCSV"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def read_csv_rows(filepath: str) -> Iterator[List[str]]:
    """Yield rows from a CSV file, skipping the header."""
    with open(filepath, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            yield row


def checkDuplicateFilenamesInCSV() -> int:
    """Check for duplicate filenames (with path) within each CSV file."""
    logging.info("VOICES: Checking for duplicate filenames in CSV files ...")
    duplicate_found = False
    for f in csv_directory.glob("*.csv"):
        seen = set()
        duplicates = set()
        for row in read_csv_rows(str(f)):
            if len(row) == 6:
                path = row[4].strip()
                fname = row[5].strip()
                key = (path, fname)
                if fname:
                    if key in seen:
                        duplicates.add(key)
                    else:
                        seen.add(key)
        for path, fname in duplicates:
            display_path = path if path else "[root]"
            logging.error(
                f"[ERROR] Duplicate filename in {f.name}: {fname} (PATH: {display_path}) appears more than once"
            )
            duplicate_found = True
    return 1 if duplicate_found else 0


def checkFilesInSoundsNotInCSV() -> int:
    """Check for .wav files in SOUNDS not referenced in any CSV file, skipping ignored folders."""
    logging.info(
        "SOUNDS: Checking for files in SOUNDS not referenced in any CSV file ..."
    )
    referenced_files = set()
    for f in csv_directory.glob("*.csv"):
        for row in read_csv_rows(str(f)):
            if len(row) == 6:
                fname = row[5].strip()
                if fname:
                    referenced_files.add(fname)
    unreferenced_found = False
    for dirpath in sound_directory.iterdir():
        if not dirpath.is_dir():
            continue
        if (dirpath / IGNORE_FILE).exists():
            continue
        for fn_path in dirpath.glob("*.wav"):
            if fn_path.name not in referenced_files:
                logging.error(f"[ERROR] Unreferenced sound file: {fn_path}")
                unreferenced_found = True
    return 1 if unreferenced_found else 0


def checkCSVcolumnCount() -> int:
    """Check that all CSV files have the expected number of columns."""
    logging.info("VOICES: Checking CSV files for missing fields ...")
    missing_csv_field = False
    for f in csv_directory.glob("*.csv"):
        with open(f, "rt") as csvfile:
            reader = csv.reader(csvfile)
            reader = ((field.strip() for field in row) for row in reader)  # Strip spaces
            try:
                header = list(next(reader))  # Read header row and convert to list
            except StopIteration:
                logging.error(f"[ERROR] {f.name}: Empty CSV file")
                missing_csv_field = True
                continue

            expected_columns = len(header)

            # Check for minimum required columns
            if expected_columns < 6:
                logging.error(
                    f"[ERROR] {f.name}: CSV header has only {expected_columns} columns (minimum 6 required)"
                )
                missing_csv_field = True
                continue

            for row in reader:
                row = list(row)
                if len(row) != expected_columns:
                    logging.error(
                        f"[ERROR] {f.name}: Expected {expected_columns} columns but got {len(row)} - {row}"
                    )
                    missing_csv_field = True
                    continue

    return 1 if missing_csv_field else 0


def checkFilenameLengthsInCSV() -> int:
    """Check that filenames in CSV files do not exceed 8 characters (excluding extension)."""
    logging.info("VOICES: Checking filename lengths in CSV files ...")
    invalid_filename_found = False
    for f in csv_directory.glob("*.csv"):
        if f.name.endswith("_scripts.csv"):
            continue
        for row in read_csv_rows(str(f)):
            row = [field.strip().strip('"') for field in row]
            if len(row) == 6:
                filename_in_csv = row[5].strip()
                if len(Path(filename_in_csv).stem) > 8:
                    logging.error(
                        f"[ERROR] {f.name}: Filename too long - {filename_in_csv}"
                    )
                    invalid_filename_found = True
    return 1 if invalid_filename_found else 0


def checkFilenameLengths() -> int:
    """Check that .wav filenames in SOUNDS do not exceed 8 characters (excluding extension)."""
    logging.info("SOUNDS: Checking file name lengths ...")
    invalid_filename_found = False
    for file_path in sound_directory.rglob("*.wav"):
        parts = file_path.parts
        if len(parts) > 2 and parts[2] == "SCRIPTS":
            continue
        elif len(file_path.stem) > 8:
            logging.error(f"[ERROR] Filename too long: {file_path}")
            invalid_filename_found = True

    return 1 if invalid_filename_found else 0


def checkNoZeroByteFiles() -> int:
    """Check for zero-byte .wav files in SOUNDS."""
    logging.info("SOUNDS: Checking for zero byte sound files ...")
    zero_byte_file_found = False
    for file_path in sound_directory.rglob("*.wav"):
        if file_path.stat().st_size == 0:
            logging.error(f"[ERROR] Zero byte file: {file_path}")
            zero_byte_file_found = True

    return 1 if zero_byte_file_found else 0


def validateSoundsJson() -> int:
    """Validate the sounds.json file."""
    logging.info("SOUNDS: Validating sounds.json ...")
    invalid_json_found = False
    with open("sounds.json") as f:
        try:
            json.load(f)
        except ValueError as err:
            logging.error(f"[ERROR] JSON not valid: {str(err)}")
            invalid_json_found = True

    return 1 if invalid_json_found else 0


def checkForDuplicateStringID() -> int:
    """Check for duplicate StringIDs in all CSV files."""
    logging.info("VOICES: Check for duplicate StringIDs ...")
    duplicate_found = False
    for f in csv_directory.glob("*.csv"):
        with open(f, "rt") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            reader = (
                (field.strip() for field in row) for row in reader
            )  # Strip spaces
            line_count = 0
            StringID_count = {}
            for row in reader:
                row = list(row)  # Convert generator to list
                if line_count == 0:
                    # absorb header row
                    line_count += 1
                else:
                    StringID = row[0]
                    if StringID in StringID_count.keys():
                        logging.error(f"[ERROR] {f}: {StringID} is duplicated")
                        StringID_count[StringID] = StringID_count[StringID] + 1
                        duplicate_found = True
                    else:
                        StringID_count[StringID] = 1

    return 1 if duplicate_found else 0


def checkCSVNewline() -> int:
    """Check that all CSV files end with a newline."""
    logging.info("VOICES: Checking CSV files for newline at the end of file ...")
    missing_newline = False
    for f in csv_directory.glob("*.csv"):
        with open(f, "r") as file:
            lines = file.readlines()
            if lines and not lines[-1].endswith("\n"):
                logging.error(f"[ERROR] {f.name}: Missing newline at end of file")
                missing_newline = True
    return 1 if missing_newline else 0


if __name__ == "__main__":
    error_count = 0
    error_count += checkCSVcolumnCount()
    error_count += checkFilenameLengthsInCSV()
    error_count += checkFilenameLengths()
    error_count += checkNoZeroByteFiles()
    error_count += validateSoundsJson()
    error_count += checkForDuplicateStringID()
    error_count += checkCSVNewline()
    error_count += checkDuplicateFilenamesInCSV()
    error_count += checkFilesInSoundsNotInCSV()

    if error_count > 0:
        sys.exit(EX_DATAERR)
    else:
        sys.exit(EX_OK)

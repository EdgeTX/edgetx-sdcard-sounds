#!/usr/bin/env python3
from typing import Iterator, List
from pathlib import Path
from functools import lru_cache

import csv
import json
import sys
import logging

from voice_generation_config import AZURE_VOICE_JOBS, GLADOS_VOICE_JOBS

# Optional: Use colorama for colored terminal output if available
try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init()
    ERROR_COLOR = Fore.RED + Style.BRIGHT
    RESET_COLOR = Style.RESET_ALL
except ImportError:
    ERROR_COLOR = ""
    RESET_COLOR = ""

EX_OK = 0
EX_DATAERR = 65

csv_directory: Path = Path("voices")
sound_directory: Path = Path("SOUNDS")
SKIP_SOUNDS_NOT_IN_CSV: str = ".skip_checkFilesInSoundsNotInCSV"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def read_csv_rows(filepath: str) -> Iterator[List[str]]:
    """Yield rows from a CSV file, skipping the header."""
    with open(filepath, "r", newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            yield row


def checkDuplicateFilenamesInCSV() -> int:
    """Check for duplicate filenames (with path) within each CSV file."""
    logging.info("VOICES: Checking for duplicate filenames in CSV files ...")
    duplicate_found = False
    for f in csv_directory.glob("*.csv"):
        seen: dict[tuple[str, str], list[str]] = {}
        duplicates = set()
        for row in read_csv_rows(str(f)):
            if len(row) >= 6:
                string_id = row[0] if row[0] else ""
                path = row[4]
                fname = row[5]
                key = (path, fname)
                if fname:
                    if key in seen:
                        seen[key].append(string_id)
                        duplicates.add(key)
                    else:
                        seen[key] = [string_id]
        for path, fname in duplicates:
            display_path = path if path else "[root]"
            string_ids = ", ".join(filter(None, seen.get((path, fname), [])))
            id_info = f" (StringIDs: {string_ids})" if string_ids else ""
            logging.error(
                f"{ERROR_COLOR}[ERROR] Duplicate filename in {f.name}: {fname} (PATH: {display_path}) appears more than once{id_info}{RESET_COLOR}"
            )
            duplicate_found = True
    return 1 if duplicate_found else 0


def checkFilesInSoundsNotInCSV() -> int:
    """Check for .wav files in SOUNDS not referenced in any CSV file, skipping ignored folders."""
    logging.info("SOUNDS: Checking for files in SOUNDS not referenced in any CSV file ...")
    referenced_files = set()
    for f in csv_directory.glob("*.csv"):
        for row in read_csv_rows(str(f)):
            if len(row) >= 6:
                path = row[4].strip()
                fname = row[5].strip()
                if fname and not path:
                    referenced_files.add(fname)
    unreferenced_found = False
    for dirpath in sound_directory.iterdir():
        if not dirpath.is_dir():
            continue
        if (dirpath / SKIP_SOUNDS_NOT_IN_CSV).exists():
            continue
        for fn_path in dirpath.glob("*.wav"):
            if fn_path.name not in referenced_files:
                logging.error(f"{ERROR_COLOR}[ERROR] Unreferenced sound file: {fn_path}{RESET_COLOR}")
                unreferenced_found = True
    return 1 if unreferenced_found else 0


@lru_cache(maxsize=1)
def getCSVOutputDirsFromGenerateScript() -> dict[str, set[str]]:
    """Return the output directories configured for each CSV in generate.py."""
    csv_output_dirs: dict[str, set[str]] = {}

    for job in (*AZURE_VOICE_JOBS, *GLADOS_VOICE_JOBS):
        csv_name = job.csv_path.name
        outdir = Path(job.langdir)
        if outdir.name == "SCRIPTS":
            outdir = outdir.parent
        csv_output_dirs.setdefault(csv_name, set()).add(str(outdir))

    return csv_output_dirs


def checkCSVReferencedFilesExistInSounds() -> int:
    """Check that all files referenced in CSV files exist in SOUNDS."""
    logging.info("SOUNDS: Checking that CSV-referenced files exist in SOUNDS ...")
    missing_found = False
    csv_output_dirs = getCSVOutputDirsFromGenerateScript()
    for f in csv_directory.glob("*.csv"):
        candidate_dirs = csv_output_dirs.get(f.name, {f.stem[:2]})
        scripts_suffix = Path("SCRIPTS") if f.name.endswith("_scripts.csv") else None
        for row in read_csv_rows(str(f)):
            if len(row) >= 6:
                path = row[4].strip()
                fname = row[5].strip()
                translation = row[2].strip() if len(row) > 2 else ""
                if fname:
                    expected_paths = []
                    for lang_dir in candidate_dirs:
                        base_path = sound_directory / lang_dir
                        if scripts_suffix is not None:
                            base_path /= scripts_suffix
                        expected_paths.append(base_path / path / fname if path else base_path / fname)
                    if not any(expected_path.exists() for expected_path in expected_paths):
                        expected_path = expected_paths[0]
                        if translation:
                            logging.error(
                                f"{ERROR_COLOR}[ERROR] {f.name}: Referenced file not found in SOUNDS: {expected_path}{RESET_COLOR}"
                            )
                            missing_found = True
                        else:
                            logging.warning(
                                f"[WARNING] {f.name}: No translation string; referenced file not found in SOUNDS: {expected_path}"
                            )
    return 1 if missing_found else 0


def checkCSVcolumnCount() -> int:
    """Check that all CSV files have the expected number of columns."""
    logging.info("VOICES: Checking CSV files for correct field count ...")
    missing_csv_field = False
    for f in csv_directory.glob("*.csv"):
        with open(f, "rt") as csvfile:
            reader = csv.reader(csvfile)
            try:
                header = next(reader)
                expected_columns = len(header)
            except StopIteration:
                logging.error(f"{ERROR_COLOR}[ERROR] {f.name}: Empty CSV file{RESET_COLOR}")
                missing_csv_field = True
                continue

            # Check for minimum required columns
            if expected_columns < 6:
                logging.error(
                    f"{ERROR_COLOR}[ERROR] {f.name}: CSV header has only {expected_columns} columns (minimum 6 required){RESET_COLOR}"
                )
                missing_csv_field = True
                continue

            # Check each row has the correct number of columns
            for row_num, row in enumerate(reader, 2):
                if len(row) != expected_columns:
                    logging.error(
                        f"{ERROR_COLOR}[ERROR] {f.name}:{row_num}: Expected {expected_columns} columns but got {len(row)}{RESET_COLOR}"
                    )
                    missing_csv_field = True

    return 1 if missing_csv_field else 0


def checkFilenameLengthsInCSV() -> int:
    """Check that filenames in CSV files do not exceed 8 characters (excluding extension)."""
    logging.info("VOICES: Checking filename lengths in CSV files ...")
    invalid_filename_found = False
    for f in csv_directory.glob("*.csv"):
        if f.name.endswith("_scripts.csv"):
            continue
        for row in read_csv_rows(str(f)):
            if len(row) >= 6:
                filename_in_csv = row[5]
                if len(Path(filename_in_csv).stem) > 8:
                    logging.error(f"{ERROR_COLOR}[ERROR] {f.name}: Filename too long - {filename_in_csv}{RESET_COLOR}")
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
            logging.error(f"{ERROR_COLOR}[ERROR] Filename too long: {file_path}{RESET_COLOR}")
            invalid_filename_found = True

    return 1 if invalid_filename_found else 0


def checkNoZeroByteFiles() -> int:
    """Check for zero-byte .wav files in SOUNDS."""
    logging.info("SOUNDS: Checking for zero byte sound files ...")
    zero_byte_file_found = False
    for file_path in sound_directory.rglob("*.wav"):
        if file_path.stat().st_size == 0:
            logging.error(f"{ERROR_COLOR}[ERROR] Zero byte file: {file_path}{RESET_COLOR}")
            zero_byte_file_found = True

    return 1 if zero_byte_file_found else 0


def validateSoundsJson() -> int:
    """Validate the sounds.json file."""
    logging.info("SOUNDS: Validating sounds.json ...")
    invalid_json_found = False
    try:
        with open("sounds.json") as f:
            json.load(f)
    except FileNotFoundError:
        logging.error(f"{ERROR_COLOR}[ERROR] sounds.json not found{RESET_COLOR}")
        invalid_json_found = True
    except ValueError as err:
        logging.error(f"{ERROR_COLOR}[ERROR] JSON not valid: {err!s}{RESET_COLOR}")
        invalid_json_found = True

    return 1 if invalid_json_found else 0


def checkForDuplicateStringID() -> int:
    """Check for duplicate StringIDs in all CSV files."""
    logging.info("VOICES: Check for duplicate StringIDs ...")
    duplicate_found = False
    for f in csv_directory.glob("*.csv"):
        StringID_count = {}
        with open(f, "rt") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    StringID = row[0]
                    if StringID in StringID_count:
                        logging.error(f"{ERROR_COLOR}[ERROR] {f.name}: {StringID} is duplicated{RESET_COLOR}")
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
                logging.error(f"{ERROR_COLOR}[ERROR] {f.name}: Missing newline at end of file{RESET_COLOR}")
                missing_newline = True
    return 1 if missing_newline else 0


def checkCSVFormatting() -> int:
    """Check that CSV files can be parsed by Python's CSV reader (standard RFC 4180)
    and that path/filename fields contain no unexpected quotes or leading/trailing spaces."""
    logging.info("VOICES: Checking CSV files can be parsed ...")
    parsing_error = False
    for f in csv_directory.glob("*.csv"):
        reader = None
        try:
            with open(f, "r", newline="") as file:
                reader = csv.reader(file, delimiter=",", quotechar='"')
                next(reader, None)  # Skip header
                for row_num, row in enumerate(reader, start=2):
                    if len(row) < 6:
                        continue
                    for col_idx, col_name in [(4, "PATH"), (5, "FILENAME")]:
                        field = row[col_idx]
                        if field != field.strip():
                            logging.error(
                                f"{ERROR_COLOR}[ERROR] {f.name}:{row_num}: {col_name} field has "
                                f"leading/trailing whitespace - {repr(field)}{RESET_COLOR}"
                            )
                            parsing_error = True
                        if '"' in field:
                            logging.error(
                                f"{ERROR_COLOR}[ERROR] {f.name}:{row_num}: {col_name} field contains "
                                f"unexpected quote character - {repr(field)}{RESET_COLOR}"
                            )
                            parsing_error = True
        except csv.Error as err:
            line_num = getattr(reader, "line_num", "?") if reader else "?"
            logging.error(
                f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: CSV parse error - {err}{RESET_COLOR}"
            )
            parsing_error = True

    return 1 if parsing_error else 0


def checkSequentialStringIDs() -> int:
    """Check that String IDs (first column) are sequential without gaps (for non-script CSV files)."""

    # CSV files where gaps should be warnings instead of errors
    WARNING_ONLY_FILES = {"fr-FR.csv", "pt-PT.csv", "uk-UA.csv"}

    logging.info("VOICES: Checking for gaps in sequential String IDs ...")
    gaps_found = False
    for f in csv_directory.glob("*.csv"):
        if f.name.endswith("_scripts.csv"):
            continue

        string_ids = []
        row_numbers = {}  # Track which row each String ID appears on
        with open(f, "rt") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            next(reader, None)  # Skip header
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                if row and row[0]:
                    try:
                        string_id = int(row[0])
                        string_ids.append(string_id)
                        row_numbers[string_id] = row_num
                    except ValueError:
                        # Skip non-numeric String IDs
                        pass

        if not string_ids:
            continue

        # Determine if this file should produce warnings or errors
        is_warning_only = f.name in WARNING_ONLY_FILES

        # Sort and check for gaps
        string_ids.sort()
        for i in range(len(string_ids) - 1):
            expected_next = string_ids[i] + 1
            actual_next = string_ids[i + 1]
            if actual_next != expected_next:
                # Report all missing IDs in the gap
                missing_ids = list(range(expected_next, actual_next))
                missing_str = ", ".join(map(str, missing_ids))

                if is_warning_only:
                    logging.warning(
                        f"[WARNING] {f.name}: Gap in String IDs - missing ID(s) {missing_str} between row {row_numbers[string_ids[i]]} (ID {string_ids[i]}) and row {row_numbers[actual_next]} (ID {actual_next})"
                    )
                else:
                    logging.error(
                        f"{ERROR_COLOR}[ERROR] {f.name}: Gap in String IDs - missing ID(s) {missing_str} between row {row_numbers[string_ids[i]]} (ID {string_ids[i]}) and row {row_numbers[actual_next]} (ID {actual_next}){RESET_COLOR}"
                    )
                    gaps_found = True

    return 1 if gaps_found else 0


if __name__ == "__main__":
    error_count = 0
    error_count += checkCSVFormatting()
    error_count += checkCSVcolumnCount()
    error_count += checkFilenameLengthsInCSV()
    error_count += checkFilenameLengths()
    error_count += checkNoZeroByteFiles()
    error_count += validateSoundsJson()
    error_count += checkForDuplicateStringID()
    error_count += checkCSVNewline()
    error_count += checkDuplicateFilenamesInCSV()
    error_count += checkFilesInSoundsNotInCSV()
    error_count += checkCSVReferencedFilesExistInSounds()
    error_count += checkSequentialStringIDs()

    if error_count > 0:
        sys.exit(EX_DATAERR)
    else:
        sys.exit(EX_OK)

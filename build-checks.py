#!/usr/bin/env python3
from typing import Iterator, List
from pathlib import Path

import csv
import json
import sys
import logging

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
        seen: dict[tuple[str, str], list[str]] = {}
        duplicates = set()
        for row in read_csv_rows(str(f)):
            if len(row) >= 6:
                string_id = row[0].strip() if row[0] else ""
                path = row[4].strip()
                fname = row[5].strip()
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
                logging.error(f"{ERROR_COLOR}[ERROR] Unreferenced sound file: {fn_path}{RESET_COLOR}")
                unreferenced_found = True
    return 1 if unreferenced_found else 0


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
            row = [field.strip().strip('"') for field in row]
            if len(row) == 6:
                filename_in_csv = row[5].strip()
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
    with open("sounds.json") as f:
        try:
            json.load(f)
        except ValueError as err:
            logging.error(f"{ERROR_COLOR}[ERROR] JSON not valid: {str(err)}{RESET_COLOR}")
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
                    StringID = row[0].strip()
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
    """Check that all CSV files are properly formatted with every field quoted."""
    logging.info("VOICES: Checking CSV files are properly formatted ...")
    formatting_error = False
    for f in csv_directory.glob("*.csv"):
        with open(f, "r") as file:
            # Read raw file to check quoting
            for line_num, line in enumerate(file, 1):
                line = line.rstrip('\n\r')
                if not line:  # Skip empty lines
                    continue
                
                # Check that every field is quoted: must start with quote
                if not line.startswith('"'):
                    logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Line does not start with quote - all fields must be quoted{RESET_COLOR}")
                    formatting_error = True
                    continue
                
                # Use csv module to parse the line and verify structure
                try:
                    reader = csv.reader([line])
                    row = next(reader)
                    
                    # Verify each field in the raw line is actually quoted
                    # by checking the original line format
                    in_quote = False
                    i = 0
                    field_quotes = 0  # Count opening quotes for fields
                    
                    while i < len(line):
                        if line[i] == '"':
                            if not in_quote:
                                # Check this quote starts a field (at position 0 or after comma)
                                if i > 0 and line[i-1] != ',':
                                    logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Unquoted content before quote at position {i+1}{RESET_COLOR}")
                                    formatting_error = True
                                    break
                                in_quote = True
                                field_quotes += 1
                            else:
                                # Check if this closes the field or is escaped
                                if i + 1 < len(line) and line[i + 1] == '"':
                                    i += 1  # Skip escaped quote
                                else:
                                    in_quote = False
                                    # Next must be comma or end of line
                                    if i + 1 < len(line) and line[i + 1] != ',':
                                        logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Unquoted content after quote at position {i+1}{RESET_COLOR}")
                                        formatting_error = True
                                        break
                        elif not in_quote and line[i] != ',':
                            # Unquoted character outside quotes
                            logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Unquoted field content at position {i+1}{RESET_COLOR}")
                            formatting_error = True
                            break
                        
                        i += 1
                    
                    if in_quote:
                        logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Unclosed quote{RESET_COLOR}")
                        formatting_error = True
                
                except Exception as e:
                    logging.error(f"{ERROR_COLOR}[ERROR] {f.name}:{line_num}: Failed to parse CSV - {str(e)}{RESET_COLOR}")
                    formatting_error = True
    
    return 1 if formatting_error else 0


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

    if error_count > 0:
        sys.exit(EX_DATAERR)
    else:
        sys.exit(EX_OK)

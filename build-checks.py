#!/usr/bin/env python3


import csv
import json
import os
import sys
import logging


csv_directory: str = "voices"
sound_directory: str = "SOUNDS"
IGNORE_FILE: str = ".skip_checkFilesInSoundsNotInCSV"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


# Check for duplicate filenames in CSV files
def checkDuplicateFilenamesInCSV() -> int:
    logging.info("VOICES: Checking for duplicate filenames in CSV files ...")
    duplicate_found = False
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith(".csv"):
            filename_count = {}
            with open(f, "r") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) == 6:
                        path = row[4].strip()
                        fname = row[5].strip()
                        key = (path, fname)
                        if fname:
                            filename_count[key] = filename_count.get(key, 0) + 1
            for (path, fname), count in filename_count.items():
                if count > 1:
                    logging.error(f"[ERROR] Duplicate filename in {filename}: {fname} (PATH: {path}) appears {count} times")
                    duplicate_found = True
    return 1 if duplicate_found else 0

# Check for files in SOUNDS that are not in CSV files
def checkFilesInSoundsNotInCSV() -> int:
    logging.info("SOUNDS: Checking for files in SOUNDS not referenced in any CSV file ...")
    # Collect all filenames referenced in CSVs
    referenced_files = set()
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith(".csv"):
            with open(f, "r") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) == 6:
                        fname = row[5].strip()
                        if fname:
                            referenced_files.add(fname)
    # Walk SOUNDS and check for unreferenced files
    unreferenced_found = False
    for dirpath, dirnames, filenames in os.walk(sound_directory):
        # Skip folder and its subfolders if .skip_checkFilesInSoundsNotInCSV exists
        if ".skip_checkFilesInSoundsNotInCSV" in filenames:
            dirnames[:] = []  # Prevent os.walk from descending into subdirs
            continue
        for fn in filenames:
            if fn.lower().endswith('.wav'):
                if fn not in referenced_files:
                    logging.error(f"[ERROR] Unreferenced sound file: {os.path.join(dirpath, fn)}")
                    unreferenced_found = True
    return 1 if unreferenced_found else 0


def checkCSVcolumnCount() -> int:
    logging.info("VOICES: Checking CSV files for missing fields ...")
    missing_csv_field = False
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith(".csv"):
            with open(f, "r") as csvfile:
                reader = csv.reader(csvfile)
                reader = ((field.strip() for field in row) for row in reader)  # Strip spaces
                header = list(next(reader))  # Read header row and convert to list
                expected_columns = len(header)
                
                # Check for minimum required columns
                if expected_columns < 6:
                    print(f"{filename}: CSV header has only {expected_columns} columns (minimum 6 required)")
                    missing_csv_field = True
                    continue
                
                for row in reader:
                        row = list(row)  # Convert generator to list
                        if not len(row) == expected_columns:
                            logging.error(f"[ERROR] {filename}: Insufficient columns of data - {row}")
                            missing_csv_field = True
                            continue

    return 1 if missing_csv_field else 0


def checkFilenameLengthsInCSV() -> int:
    logging.info("VOICES: Checking filename lengths in CSV files ...")
    invalid_filename_found = False
    for filename in os.listdir(csv_directory):
        if filename.endswith("_scripts.csv"):
            continue
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith(".csv"):
            with open(f, "r") as csvfile:
                reader = csv.reader(csvfile)
                reader = ((field.strip().strip('"') for field in row) for row in reader)  # Strip spaces and quotes
                next(reader)  # Skip the header row
                for row in reader:
                    row = list(row)  # Convert generator to list
                    if len(row) == 6:
                        filename_in_csv = row[5].strip()  # Ensure filename is stripped
                        if (len(os.path.splitext(filename_in_csv)[0]) > 8):
                            logging.error(f"[ERROR] {filename}: Filename too long - {filename_in_csv}")
                            invalid_filename_found = True
    return 1 if invalid_filename_found else 0


def checkFilenameLengths() -> int:
    logging.info("SOUNDS: Checking file name lengths ...")
    invalid_filename_found = False
    for dirpath, dirnames, filenames in os.walk(sound_directory):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            # Only check .wav files
            if not fn.lower().endswith('.wav'):
                continue
            # Don't check SCRIPTS length - not ours to manage
            if path.split(os.path.sep)[2] == "SCRIPTS":
                continue
            elif len(os.path.splitext(fn)[0]) > 8:
                logging.error(f"[ERROR] Filename too long: {path}")
                invalid_filename_found = True

    return 1 if invalid_filename_found else 0


def checkNoZeroByteFiles() -> int:
    logging.info("SOUNDS: Checking for zero byte sound files ...")
    zero_byte_file_found = False
    for root, dirs, files in os.walk(sound_directory):
        path = root.split(os.sep)
        for fn in files:
            if not fn.lower().endswith('.wav'):
                continue
            path = os.path.join(root, fn)
            if os.stat(path).st_size == 0:
                logging.error(f"[ERROR] Zero byte file: {path}")
                zero_byte_file_found = True

    return 1 if zero_byte_file_found else 0


def validateSoundsJson() -> int:
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
    logging.info("VOICES: Check for duplicate StringIDs ...")
    duplicate_found = False
    pathName = os.path.join(os.getcwd(), csv_directory)

    voiceFiles = []
    # scan for voice CSV files
    fileNames = os.listdir(pathName)
    for fileNames in fileNames:
        if fileNames.endswith(".csv"):
            voiceFiles.append(fileNames)

    # iterate over files found
    for filename in voiceFiles:
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f):
            with open(f, "rt") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", quotechar='"')
                reader = ((field.strip() for field in row) for row in reader)  # Strip spaces
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
    logging.info("VOICES: Checking CSV files for newline at the end of file ...")
    missing_newline = False
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith(".csv"):
            with open(f, "r") as file:
                lines = file.readlines()
                if lines and not lines[-1].endswith("\n"):
                    logging.error(f"[ERROR] {filename}: Missing newline at end of file")
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
        sys.exit(os.EX_DATAERR)
    else:
        sys.exit(os.EX_OK)

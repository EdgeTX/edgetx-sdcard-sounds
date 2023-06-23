#!/usr/bin/env python3

import csv
import json
import os
import sys

csv_directory = 'voices'
sound_directory = 'SOUNDS'

# TODO: Check for duplicate filenames in CSV files
# TODO: Check for files in SOUNDS that are not in CSV files


def checkCSVcolumnCount():
    print("VOICES: Checking CSV files for missing fields ...")
    missing_csv_field = False
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith('.csv'):
            reader = csv.reader(open(f, "r"))
            for row in reader:
                if not len(row) == 6:
                    print("{}: Insufficient columns of data - {}".format(filename, row))
                    missing_csv_field = True
                    continue

    if missing_csv_field:
        return 1
    else:
        return 0

def checkFilenameLengths():
    print("SOUNDS: Checking file name lengths ...")
    invalid_filename_found = False
    for dirpath, dirnames, filenames in os.walk(sound_directory):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            if path.split(os.path.sep)[2] == "SYSTEM":
                if len(os.path.splitext(fn)[0]) > 8:
                    print("Filename too long for a SYSTEM file: {}".format(path))
                    invalid_filename_found = True
            elif path.split(os.path.sep)[2] == "SCRIPTS":
                continue
            elif len(os.path.splitext(fn)[0]) > 6:
                print("Filename too long for a non-SYSTEM file: {}".format(path))
                invalid_filename_found = True

    if invalid_filename_found:
        return 1
    else:
        return 0


def checkNoZeroByteFiles():
    print("SOUNDS: Checking for zero byte sound files ...")
    zero_byte_file_found = False
    for root, dirs, files in os.walk(sound_directory):
        path = root.split(os.sep)
        for fn in files:
            path = os.path.join(root, fn)
            if os.stat(path).st_size == 0:
                print("Zero byte file: {}".format(path))
                zero_byte_file_found = True

    if zero_byte_file_found:
        return 1
    else:
        return 0


def validateSoundsJson():
    print("SOUNDS: Validating sounds.json ...")
    invalid_json_found = False
    f = open("sounds.json")
    try:
        json.load(f)
    except ValueError as err:
        print("JSON not valid: {}".format(str(err)))
        invalid_json_found = True

    if invalid_json_found:
        return 1
    else:
        return 0

def checkForDuplicateStringID():
    print("VOICES: Check for duplicate StringIDs ...")
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
            with open(f, 'rt') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                line_count = 0
                StringID_count = {}
                for row in reader:
                    if line_count == 0:
                        # absorb header row
                        line_count += 1
                    else:
                        StringID = row[0]
                        if StringID in StringID_count.keys():
                            print('{}: {} is duplicated'.format(f, StringID))
                            StringID_count[StringID] = StringID_count[StringID] + 1
                            duplicate_found = True
                        else:
                            StringID_count[StringID] = 1

    if duplicate_found:
        return 1
    else:
        return 0


if __name__ == "__main__":
    error_count = 0
    error_count += checkCSVcolumnCount()
    error_count += checkFilenameLengths()
    error_count += checkNoZeroByteFiles()
    error_count += validateSoundsJson()
    error_count += checkForDuplicateStringID()

    if error_count > 0:
        sys.exit(os.EX_DATAERR)
    else:
        sys.exit(os.EX_OK)

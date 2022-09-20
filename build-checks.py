#!/usr/bin/env python3

import csv
import os
import sys

csv_directory = 'voices'
sound_directory = 'SOUNDS'

## TODO: Check for duplicate filenames in CSV files
## TODO: Check for files in SOUNDS that are not in CSV files
## TODO: Check CSV for correct row indexes


def checkCSVcolumnCount():
    print("VOICES: Checking CSV files for missing fields ...")
    for filename in os.listdir(csv_directory):
        f = os.path.join(csv_directory, filename)
        if os.path.isfile(f) and filename.endswith('.csv'):
            reader = csv.reader(open(f, "r"))
            for row in reader:
                if not len(row) == 6:
                    print("{}: Insufficient columns of data - {}".format(filename, row))
                    continue


def checkFilenameLengths():
    print("SOUNDS: Checking file name lengths ...")
    for dirpath, dirnames, filenames in os.walk(sound_directory):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            if path.split(os.path.sep)[2] == "SYSTEM":
                if len(os.path.splitext(fn)[0]) > 8:
                    print("Filename too long for a SYSTEM file: {}".format(path))
            elif path.split(os.path.sep)[2] == "SCRIPTS":
                continue
            elif len(os.path.splitext(fn)[0]) > 6:
                print("Filename too long for a non-SYSTEM file: {}".format(path))


def checkNoZeroByteFiles():
    print("SOUNDS: Checking for zero byte sound files ...")
    for root, dirs, files in os.walk(sound_directory):
        path = root.split(os.sep)
        for fn in files:
            path = os.path.join(root, fn)
            if os.stat(path).st_size == 0:
                print("Zero byte file: {}".format(path))


if __name__ == "__main__":
    checkCSVcolumnCount()
    checkFilenameLengths()
    checkNoZeroByteFiles()

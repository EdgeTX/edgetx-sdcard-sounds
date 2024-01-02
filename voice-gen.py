#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""
    Importing the Speech SDK for Python failed.
    Refer to
    https://docs.microsoft.com/azure/cognitive-services/speech-service/quickstart-text-to-speech-python for
    installation instructions.
    """)
    sys.exit(1)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [FILE] [VOICE] [LANGDIR]",
        description="Generate voice packs from CSV list."
    )

    parser.add_argument(
        "-v", "--version", action="version",
        version=f"{parser.prog} version 1.0.0"
    )

    parser.add_argument('file',
                        type=str,
                        help="CSV Translation file"
                        )

    parser.add_argument('voice',
                        type=str,
                        help="Voice to use"
                        )

    parser.add_argument('-l',
                        '--locale',
                        type=str,
                        help="Language locale",
                        required=False,
                        )

    parser.add_argument('langdir',
                        type=str,
                        help="Language subfolder"
                        )

    parser.add_argument('-p',
                        '--pitch',
                        help="Pitch adjustment",
                        type=str,
                        default="default")

    parser.add_argument('-r',
                        '--rate',
                        help="Rate adjustment",
                        type=str,
                        default="default")

    parser.add_argument('-s',
                        '--delay',
                        type=int,
                        help="Sleep time processing each translation",
                        required=False,
                        default='3'
                        )

    return parser


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    csv_file = args.file
    csv_rows = 0
    voice = args.voice
    langdir = args.langdir
    basedir = os.path.dirname(os.path.abspath(__file__))
    outdir = ""
    pitch = args.pitch
    rate = args.rate
    delay_time = args.delay

    if args.locale is not None:
        locale = args.locale
    else:
        locale = re.split('([a-z]{2}-[A-Z]{2})', voice)[1]

    if pitch != "default":
        pitch = pitch.replace("dn", "-").replace("up", "+")

    if rate != "default":
        rate = rate.replace("dn", "-").replace("up", "+")

    try:
        speech_key = os.environ['COGNITIVE_SERVICE_API_KEY']
        service_region = os.environ['SERVICE_REGION']
    except KeyError:
        key_file = Path('key')
        region_file = Path('region')

        try:
            if key_file.is_file() and region_file.is_file():
                with open('key', 'r') as f:
                    speech_key = f.read().strip()

                with open('region', 'r') as f:
                    service_region = f.read().strip()
            else:
                print("ERROR: Please set the environment variables for Speech and Service Region or create key and region config files.")
                sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

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

                if not os.path.exists(outdir):
                    os.makedirs(outdir)

                if text is None or text == "":
                    print(
                        f'[{line_count}/{csv_rows}] Skipping as no text to translate')
                    continue

                if not os.path.isfile(outfile):
                    print(
                        f'[{line_count}/{csv_rows}] Translate "{en_text}" to "{text}", save as "{outdir}{os.sep}{filename}".')
                    audio_config = speechsdk.audio.AudioOutputConfig(
                        filename=outfile)
                    synthesizer = speechsdk.SpeechSynthesizer(
                        speech_config=speech_config, audio_config=audio_config)

                    ssml_text = f"""
                        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{locale}">
                            <voice name="{voice}">
                                <prosody pitch="{pitch}" rate="{rate}">{text}</prosody>
                            </voice>
                        </speak>"""

                    result = synthesizer.speak_ssml_async(ssml=ssml_text).get()

                    # If failed, show error, remove empty/corrupt file and halt
                    if result.reason == speechsdk.ResultReason.Canceled:
                        cancellation_details = result.cancellation_details
                        print("Speech synthesis canceled: {}".format(
                            cancellation_details.reason))
                        if cancellation_details.reason == speechsdk.CancellationReason.Error:
                            print("Error details: {}".format(
                                cancellation_details.error_details))
                        if os.path.isfile(outdir + os.sep + filename):
                            os.remove(outdir + os.sep + filename)
                        sys.exit(1)

                    time.sleep(delay_time)

                else:
                    print(
                        f'[{line_count}/{csv_rows}] Skipping "{filename}" as already exists.')

                line_count += 1

        print(f'Finished processing {csv_rows} entries from "{csv_file}".')


if __name__ == "__main__":
    main()

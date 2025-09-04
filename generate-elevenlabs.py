import csv
import os
import subprocess
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

load_dotenv()
client = ElevenLabs()

# Getting API key from environment variable
# set the variable by:
# export ELEVENLABS_API_KEY="<Api key>"
api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    raise RuntimeError("Environment variable ELEVENLABS_API_KEY not set. Use command:\nexport ELEVENLABS_API_KEY=""<Api key>""")

# Init ElevenLabs
client = ElevenLabs(api_key=api_key)

# Array of languages
# file, voice ID, language subdir
languages = [
    ("voices/pl-PL.csv", "EXAVITQu4vr4xnSDxMaL", "pl"),
    # Add other languages here
]

for csv_file, voice_name, output_dir in languages:
    print(f"\nProcesing file {csv_file}")

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if not row.get("Filename") or row.get("String ID", "").startswith("#"):
                continue

            name = row["Filename"].split('.')[0]
            tr = row.get("Translation", "")
            subd = row.get("Path", "")  # Subdirectory

            full_dir = os.path.join("SOUNDS", output_dir, subd)
            os.makedirs(full_dir, exist_ok=True)
            output_mp3 = os.path.join(full_dir, f"{name}.mp3")
            output_wav = os.path.join(full_dir, f"{name}.wav")

            # To save free tokens available on Elevenlabs - skip existing files to avoid double generating
            if os.path.exists(output_wav):
                # print(f"\n\nWAV file exist, skipping: {output_wav}")
                continue

            print(f"\n\nGenerating MP3 file: {output_mp3} ...")

            audio_generator = client.text_to_speech.convert(
                text=tr,
                voice_id=voice_name,          
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )

            audio_bytes = b''.join(audio_generator)

            with open(output_mp3, "wb") as out_file:
                out_file.write(audio_bytes)

            print(f"MP3 saved: {output_mp3}")



            # Conversion MP# -> WAV using ffmpeg command
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # overwrite existing file
                "-i", output_mp3,
                "-ar", "32000",   # sample rate 32 kHz
                "-ac", "1",       # mono
                "-sample_fmt", "s16",  # 16-bit PCM
                output_wav
            ]

            subprocess.run(ffmpeg_cmd, check=True)
            print(f"WAV for EdgeTX saved: {output_wav}")

            # Remove temporary mp3 file
            if os.path.exists(output_mp3):
                os.remove(output_mp3)
        


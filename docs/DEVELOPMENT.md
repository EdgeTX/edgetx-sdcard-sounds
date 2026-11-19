# Voice pack development

This document covers how the voice packs in this repository are defined, generated, checked and released. For ways to help that don't involve code (feedback, reporting translation or pronunciation errors, requesting a language) see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Repository layout

- `voices/*.csv`: one file per language and voice set, listing every audio file and the text to speak. `*_scripts.csv` files hold the audio for the Lua scripts (Betaflight, iNav, Yaapu) and end up under `SOUNDS/<lang>/SCRIPTS/`.
- `SOUNDS/<lang>/`: the generated audio, committed to the repository. `SOUNDS/<lang>/SYSTEM/` holds the files the firmware plays itself (numbers, units, system alerts).
- `voice_generation_config.py`: which CSV is generated with which voice into which `SOUNDS` folder.
- `sounds.json`: the voice packs offered for download. Add an entry only once a pack's audio exists.
- `generate.py`, `voice-gen-azure.py`, `voice-gen-elevenlabs.py`, `voice-gen-glados.py`: audio generation.
- `build_checks.py`: consistency checks run in CI. `release.py`: builds the release archives.

## Voice CSV files

Each row describes one audio file. The columns are:

| Column | Meaning |
|---|---|
| `String ID` | Row number. Must be unique and, except in `*_scripts.csv`, sequential without gaps. |
| `Source text` | The English text, for reference. |
| `Translation` | The text that is spoken. Rows with an empty translation are skipped when generating audio. |
| `Context` | Notes for translators, e.g. which grammatical form is needed. |
| `Path` | Subfolder under `SOUNDS/<lang>/`, e.g. `SYSTEM`, or empty. |
| `Filename` | The audio file name. At most 8 characters before `.wav`, except in `*_scripts.csv`. |

`build_checks.py` also checks that every translated row has its audio file in `SOUNDS`, that `SOUNDS` contains no files missing from the CSVs, that there are no duplicate filenames or String IDs, and that each CSV ends with a newline. A row without a translation and without audio is only a warning.

### Number and unit files defined by the firmware

The firmware builds spoken numbers, units and durations from the files in `SOUNDS/<lang>/SYSTEM/`. Which files exist, and what each one must say, is decided per language by the firmware's `radio/src/translations/tts/tts_<lang>.cpp` in [EdgeTX/edgetx](https://github.com/EdgeTX/edgetx). Languages with grammatical number or gender agreement (for example Arabic, Czech, Polish, Russian, Slovak and Ukrainian) use more files, or different numbering, than English.

When translating or editing these rows:

- Don't rename, renumber or remove `SYSTEM` number and unit files. The firmware looks them up by name.
- Read the `Context` column, and if in doubt the language's `tts_<lang>.cpp`, to see which form a file needs.

#### Arabic (ar-SA)

The layout is defined by `tts_ar.cpp` (EdgeTX 3.0 and later):

- `0000`-`0099` are the numbers 0-99 in the form used with **masculine** nouns, and `0200`-`0299` the form used with **feminine** nouns. Gender polarity for 3-10 is part of the recording (e.g. `0003` = ثلاثة, `0203` = ثلاث).
- `0109`-`0112` are the four forms of ألف (ألف, ألفان, آلاف, ألفًا).
- Each unit has 4 files: `<unit>0` singular, `<unit>1` dual, `<unit>2` plural (3-10) and `<unit>3` accusative singular (11-99).
- The `Context` column of each row gives the gender the firmware assumes for that unit. If a unit's Arabic noun is changed to one of the other gender, `tts_ar.cpp` must be updated to match.

## Generating audio

### Azure Text-to-Speech

Most voice packs use Microsoft Azure neural voices.

You need [uv](https://docs.astral.sh/uv/) and `ffmpeg`. The Python dependencies, including the Azure Speech SDK and `ffmpeg-normalize`, are installed by uv. You also need an [Azure Speech resource](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/) (there is a free tier), with its key and region. The simplest way to provide them is a `.env` file in the repository root, which the generation scripts load automatically and which is listed in `.gitignore` so it can't be committed by accident:

```bash
COGNITIVE_SERVICE_API_KEY=<your key>
SERVICE_REGION=<your region>
```

Environment variables with the same names work too, and take precedence over `.env`.

To generate every job listed in `voice_generation_config.py`:

```bash
uv run ./generate.py
```

To generate a single CSV:

```bash
uv run ./voice-gen-azure.py voices/ar-SA.csv ar-SA-ZariyahNeural ar
```

Existing audio files are not regenerated, so delete a file to regenerate it.

The Azure voices have been picked from the [neural voices](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=speechtotext#prebuilt-neural-voices) offered by Microsoft Azure text to speech service, in order to get as close as possible to human-like voices. If you want to see what voices are available, and try different phrases, [check out the online demo generator](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/#features). Using some recording software, you could even save your own phrases and use them in the voice packs.

### Generating custom phrases with the Azure REST API

If you have a [Azure Speech Services subscription](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/) (there is a free usage tier), phrases can be generated with `curl` or a `http` client like `postman`. After building a text to speech resource in `Azure` you can use it by `REST` calls (`http` requests).

The request url is:
`https://<YOUR_RESOURCE_REGION>.tts.speech.microsoft.com/cognitiveservices/v1`

You should add the following headers to your request:

```
Ocp-Apim-Subscription-Key: <YOUR_RESOURCE_KEY>
Content-Type: application/ssml+xml
X-Microsoft-OutputFormat: riff-8khz-16bit-mono-pcm
```

**Note:** EdgeTX supports up to 32khz `.wav` file but in that range 8khz is the highest value supported by the conversion service. However, it is possible to select higher quality like `riff-48khz-16bit-mono-pcm` and convert to 32khz afterwards with another tool (i.e. `ffmpeg -i input.wav -ar 32000 output.wav`) if you want the best possible audio quality.

And in the request body (raw) place your `ssml` (change the voice name according to your preference, the full list is [here](https://learn.microsoft.com/azure/cognitive-services/speech-service/language-support?tabs=stt-tts)):

```
<speak version='1.0' xml:lang='en-US'>
    <voice xml:lang='en-US' xml:gender='Female' name='en-US-MichelleNeural'>YOUR_PHRASE_HERE</voice>
</speak>
```

In order to tweak some parameters of voice generation (i.e. rate, pitch) refer to the [SSML markup documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice) for values and `voice_generation_config.py` (per-voice `pitch` and `rate`) with `voice-gen-azure.py` to see how they are applied.

### ElevenLabs

The Polish voice pack is generated with ElevenLabs.

Files are generated using [ElevenLabs](https://elevenlabs.io/app/speech-synthesis/text-to-speech) voice synthesis. There are 10k tokens available for free.

Voice: Sarah

ElevenMultilingual v2.

#### One file at a time

Ubuntu commands to prepare wav file from mp3:

- Normal way:

  ```bash
  ffmpeg -i ElevenLabs_2025-09-03T16_24_21_Sarah_pre_sp100_s50_sb75_se0_b_m2.mp3 -ar 32000 -ac 1 -sample_fmt s16 engstp.wav
  ```

- To cut out words added for correct accent (0.5sec from beginning):

  ```bash
  ffmpeg -ss 0.5 -i ElevenLabs_2025-09-03T16_24_21_Sarah_pre_sp100_s50_sb75_se0_b_m2.mp3 -ar 32000 -ac 1 -sample_fmt s16 engstp.wav
  ```

- Many files at once from the same folder:

  ```bash
  for f in *.mp3; do
  ffmpeg -i "$f" -ar 32000 -ac 1 -sample_fmt s16 "${f%.mp3}.wav"
  done
  ```

#### Automated way

```bash
sudo apt update
sudo apt install libportaudio2 portaudio19-dev libasound-dev -y
pip install elevenlabs python-dotenv
```

If you don't have venv configured or enabled:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Set the API key, either as `ELEVENLABS_API_KEY=<API_KEY>` in the `.env` file (see [Azure Text-to-Speech](#azure-text-to-speech)) or as an environment variable:

```bash
export ELEVENLABS_API_KEY="<API_KEY>"
```

Optionally add your languages to array:

```bash
languages = [
    ("voices/pl-PL.csv", "EXAVITQu4vr4xnSDxMaL", "pl"),
    # Add other languages here
]
```

And finally run script to generate all the files. Script is smart and skips already generated files to not use tokens from ElevenLabs.

```bash
python3 voice-gen-elevenlabs.py
```

### Google Cloud Text-to-Speech

The Korean voice pack was generated with Google Cloud Text-to-Speech (Wavenet-B), as 16-bit PCM WAV, mono, 32 kHz, from `voices/ko-KR.csv` (system phrases) and `voices/ko-KR_scripts.csv` (numbers and script terms). Generation activity can be traced via the public [Google Cloud Logs Console](https://console.cloud.google.com/logs/query?project=tx16s-korean-ver).

## Checks and tests

```bash
uv run ./build_checks.py
uv run pytest
```

Both run in CI on pull requests.

## Releases

```bash
uv run ./release.py
```

`release.py` trims and normalises the audio with `ffmpeg` and `ffmpeg-normalize` and builds the release archives. Releases are built by CI when a `v*` tag is pushed (`.github/workflows/build_release.yml`).

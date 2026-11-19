# EdgeTX - Voice packs

This repository contains the files needed to generate the voice packages used in EdgeTX.

The currently supported languages are:

- Arabic
- Chinese Mandarin
- Chinese Taiwan Mandarin
- Chinese Hongkong Cantonese
- Chilean Spanish
- Czech
- Danish
- English
- French
- German
- Italian
- Japanese
- Korean
- Polish
- Portuguese
- Russian
- Spanish
- Swedish
- Ukrainian

The following languages are not yet supported:

- Dutch
- Hungarian
- Slovak

## Directory structure

### SOUNDS

This folder has the audio files already processed and separated by language.

To use them, the language folder (for example, `en`) must be under the `SOUNDS` folder of your `SDCARD`. With the folder added, go to the EdgeTX settings menu and select the language of the audio language that will be used (eg English).

To use any audio on your switches, first copy the file you want to use to your language folder, then you can use this file in your `Global Functions` or `Special Functions` by selecting a switch for the function and choosing the `Play track` option.

#### SCRIPTS

Inside the language folder there is a folder called `SCRIPTS`, which has audio files for commonly used LUA scripts. These audio files are generated with the same voice as the other audio files of their language pack. Each script has their own folder.

##### BETAFLIGHT

Audio files for [Betaflight TX Lua Scripts](https://github.com/betaflight/betaflight-tx-lua-scripts). Copy the WAV files from `SOUNDS/<lang>/SCRIPTS/BETAFLIGHT/` to `SOUNDS/en/` to overwrite the original audio files of the script.

##### INAV

Audio files for [iNav Lua Telemetry Flight Status](https://github.com/iNavFlight/OpenTX-Telemetry-Widget). Copy the WAV files from `SOUNDS/<lang>/SCRIPTS/INAV/` to `SCRIPTS/TELEMETRY/iNav/<lang>/` to overwrite the original audio files of the script.

##### YAAPU

Audio files for [Yaapu Telemetry Script and Widget](https://github.com/yaapu/FrskyTelemetryScript). Copy the WAV files from `SOUNDS/<lang>/SCRIPTS/YAAPU/` to `SOUNDS/yaapu0/<lang>/` to overwrite the original audio files of the script.

## Voice pack notes

### Arabic (ar-SA)

- Generated with Azure Text-to-Speech, voice `ar-SA-ZariyahNeural`. Files are in `SOUNDS/ar`. Needs EdgeTX 3.0 or later.
- Translations by [@GyroGhost](https://github.com/GyroGhost). Feedback and corrections are welcome; please open an issue.

### Korean (ko-KR)

- Generated with Google Cloud Text-to-Speech (Wavenet-B). Files are in `SOUNDS/ko`.
- Developed and contributed by [@siyeongjang](https://github.com/siyeongjang), a Korean RC enthusiast, to improve accessibility and user experience for Korean-speaking pilots.
- Feedback or improvement suggestions are welcome. Please feel free to open an issue.

### Polish (pl-PL)

- Generated with [ElevenLabs](https://elevenlabs.io/) (voice Sarah, Multilingual v2). Files are in `SOUNDS/pl`.

## Alternatives

- Mike has created a python script that can be used to generate the audio using Googles Text to Speech service - https://github.com/xsnoopy/edgetx-sdcard-sounds
- The OpenTX Speaker voice generator (Windows only) uses the built in text to speech engine of Microsoft Windows, and can be used to generate new audio also. https://www.open-tx.org/2014/03/15/opentx-speaker
- Record your operating systems own text-to-speech narration capability
- Get audio from Google Translate - as shown in #106
- Google Docs - using text to speech addons
- [TTSMAKER](https://ttsmaker.com/)
- [NaturalReader](https://www.naturalreaders.com/)
- [Speechify](https://speechify.com/)
- [ReadSpeaker](https://www.readspeaker.com/)
- [iSpeech](https://www.ispeech.org/)
- [Amazon Polly](https://aws.amazon.com/polly/)
- macOS `say` command (with Siri voices) then add `-ar 16000 -ac 1 -sample_fmt s16` to ffmpeg

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For how the voice packs are defined, generated and released, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

# EdgeTX - Voice packs

This repository contains the files needed to generate the voice packages used in EdgeTX.

The currently supported languages are:
* Chinese Mandarin
* Chinese Taiwan Mandarin
* Chilean Spanish
* Czech
* Danish
* English
* French
* German
* Italian
* Japanese
* Portuguese
* Russian
* Spanish
* Swedish

The following languages are not yet supported:
* Dutch
* Hungarian
* Slovak

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

## Voices

All of the voices used in the EdgeTX voice packs have been picked from the [neural voices](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=speechtotext#prebuilt-neural-voices) offered by Microsoft Azure text to speech service, in order to get as close as possible to human-like voices. If you want to see what voices are available, and try different phrases, [check out the online demo generator](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/#features). Using some recording software, you could even save your own phrases and use them in the voice packs.

### Generating custom phrases
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

## How to build yourself

In order to generate the voice packages and do the release processing, you will need a Linux environment to run in.
Ubuntu 18.04 is recommended as it is a LTS release. Newer versions and other flavours of Linux will most likely work also, but are not supported.

You will also need to have `ffmpeg`, `spx` and `ffmpeg-normalize` packages installed.

`ffmpeg` is used to clip any silence from the audio files. `ffmpeg-normalise` is used to normalise the audio files.
`spx` is the tool that generates the audio files using Microsoft Azure Text to Speech processing.

Installing SPX can be a little tricky, but can be installed as follows:

```bash
wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update; \
  sudo apt-get install -y apt-transport-https && \
  sudo apt-get update && \
  sudo apt-get install -y dotnet-sdk-3.1

dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI
```

After you have installed SPX, you will also need to [create a Microsoft Azure account](https://azure.microsoft.com/en-us/services/cognitive-services/speech-to-text/) if you don't have one already. There are both free and paid options, but the free one is sufficient for this purpose - it is just rate limited. After you have done that, [follow the quick start guide](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/spx-basics) to configure the required region and subscription keys.

## Alternatives
- Mike has created a python script that can be used to generate the audio using Googles Text to Speech service - https://github.com/xsnoopy/edgetx-sdcard-sounds
- The OpenTX Speaker voice generator (Windows only) uses the built in text to speech engine of Microsoft Windows, and can be used to generate new audio also. https://www.open-tx.org/2014/03/15/opentx-speaker



## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

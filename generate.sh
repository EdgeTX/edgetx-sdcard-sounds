#!/bin/bash

# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory
cd "${script_dir}" || exit 1

if ! command -v ffmpeg-normalize >/dev/null 2>&1; then
    if ! uv run --quiet ffmpeg-normalize --version >/dev/null 2>&1; then
        echo "Error: ffmpeg-normalize not found in PATH or uv environment." >&2
        exit 1
    fi
fi

check_dependencies() {
    if [ ! -f "${script_dir}/voice-gen.py" ]; then
        echo "Script halt: voice-gen.py not found in '${script_dir}'"
        exit 1
    fi
}

check_file_exists() {
    if [ ! -f "$1" ]; then
        echo "Error: File $1 not found!" >&2
        exit 1
    fi
}

check_dependencies
check_file_exists "${script_dir}/voice-gen.py"
check_file_exists "${script_dir}/voice-gen-glados.py"

# Delete logs from previous pass
find . -name "*.log" -delete

# Azure TTS voice configurations
voices=(
    "./voices/cs-CZ.csv cs-CZ-VlastaNeural cz"
    "./voices/da_DK.csv da-DK-ChristelNeural da"
    "./voices/da_DK_scripts.csv da-DK-ChristelNeural da/SCRIPTS"
    "./voices/de-DE.csv de-DE-KatjaNeural de"
    "./voices/en-GB.csv en-IE-EmilyNeural en --rate '1.10'"
    "./voices/en-GB_scripts.csv en-IE-EmilyNeural en/SCRIPTS --rate '1.10'"
    "./voices/en-GB.csv en-GB-LibbyNeural en_gb-libby"
    "./voices/en-GB_scripts.csv en-GB-LibbyNeural en_gb-libby/SCRIPTS"
    "./voices/en-GB.csv en-GB-RyanNeural en_gb-ryan"
    "./voices/en-GB_scripts.csv en-GB-RyanNeural en_gb-ryan/SCRIPTS"
    "./voices/en-US.csv en-US-GuyNeural en_us-guy"
    "./voices/en-US_scripts.csv en-US-GuyNeural en_us-guy/SCRIPTS"
    "./voices/en-US.csv en-US-MichelleNeural en_us-michelle"
    "./voices/en-US_scripts.csv en-US-MichelleNeural en_us-michelle/SCRIPTS"
    "./voices/en-US.csv en-US-SaraNeural en_us-sara"
    "./voices/en-US_scripts.csv en-US-SaraNeural en_us-sara/SCRIPTS"
    "./voices/es-CL.csv es-CL-CatalinaNeural es_cl-catalina"
    "./voices/es-ES.csv es-ES-ElviraNeural es"
    "./voices/fr-FR.csv fr-FR-DeniseNeural fr"
    "./voices/it-IT.csv it-IT-ElsaNeural it"
    "./voices/it-IT_scripts.csv it-IT-ElsaNeural it/SCRIPTS"
    "./voices/ja-JP.csv ja-JP-NanamiNeural jp"
    "./voices/ja-JP_scripts.csv ja-JP-NanamiNeural jp/SCRIPTS"
    "./voices/pt-PT.csv pt-BR-FranciscaNeural pt"
    "./voices/ru-RU.csv ru-RU-SvetlanaNeural ru"
    "./voices/sv-SE.csv sv-SE-SofieNeural se --pitch 'dn10%' --rate '0.9'"
    "./voices/sv-SE_scripts.csv sv-SE-SofieNeural se/SCRIPTS --pitch 'dn10%' --rate '0.9'"
    "./voices/uk-UA.csv uk-UA-OstapNeural ua-ostap"
    "./voices/uk-UA.csv uk-UA-PolinaNeural ua-polina"
    "./voices/zh-CN.csv zh-CN-XiaoxiaoNeural cn"
    "./voices/zh-TW.csv zh-TW-HsiaoChenNeural tw"
    "./voices/zh-HK.csv zh-HK-HiuGaaiNeural hk --rate '0.9'"
)

# Loop through the Azure TTS configurations
for voice in "${voices[@]}"; do
    # Use eval to handle parameters with spaces (e.g., --pitch and --rate)
    eval "uv run ./voice-gen.py ${voice}" || exit 1
done

# GLaDOS-specific configurations
glados_voices=(
    "./voices/en-GB.csv en_gb-glados"
    "./voices/en-GB_scripts.csv en_gb-glados/SCRIPTS"
)

# Loop through the GLaDOS configurations
for glados_voice in "${glados_voices[@]}"; do
    eval "uv run ./voice-gen-glados.py ${glados_voice}" || exit 1
done


# ElevenLabs (single run, internal config)
uv run ./voice-gen-elevenlabs.py || exit 1

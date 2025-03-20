#!/bin/bash

# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory
cd "${script_dir}" || exit 1

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

# Generate voices
"./voice-gen.py" "./voices/cs-CZ.csv" cs-CZ-VlastaNeural cz || exit 1
"./voice-gen.py" "./voices/da_DK.csv" da-DK-ChristelNeural da || exit 1
"./voice-gen.py" "./voices/da_DK_scripts.csv" da-DK-ChristelNeural da/SCRIPTS || exit 1
"./voice-gen.py" "./voices/de-DE.csv" de-DE-KatjaNeural de || exit 1
"./voice-gen.py" "./voices/en-GB.csv" en-IE-EmilyNeural en || exit 1
"./voice-gen.py" "./voices/en-GB_scripts.csv" en-IE-EmilyNeural en/SCRIPTS || exit 1
"./voice-gen.py" "./voices/en-GB.csv" en-GB-LibbyNeural en_gb-libby || exit 1
"./voice-gen.py" "./voices/en-GB_scripts.csv" en-GB-LibbyNeural en_gb-libby/SCRIPTS || exit 1
"./voice-gen.py" "./voices/en-GB.csv" en-GB-RyanNeural en_gb-ryan || exit 1
"./voice-gen.py" "./voices/en-GB_scripts.csv" en-GB-RyanNeural en_gb-ryan/SCRIPTS || exit 1
"./voice-gen-glados.py" "./voices/en-GB.csv" en_gb-glados || exit 1
"./voice-gen-glados.py" "./voices/en-GB_scripts.csv" en_gb-glados/SCRIPTS || exit 1
"./voice-gen.py" "./voices/en-US.csv" en-US-GuyNeural en_us-guy || exit 1
"./voice-gen.py" "./voices/en-US_scripts.csv" en-US-GuyNeural en_us-guy/SCRIPTS || exit 1
"./voice-gen.py" "./voices/en-US.csv" en-US-MichelleNeural en_us-michelle || exit 1
"./voice-gen.py" "./voices/en-US_scripts.csv" en-US-MichelleNeural en_us-michelle/SCRIPTS || exit 1
"./voice-gen.py" "./voices/en-US.csv" en-US-SaraNeural en_us-sara || exit 1
"./voice-gen.py" "./voices/en-US_scripts.csv" en-US-SaraNeural en_us-sara/SCRIPTS || exit 1
"./voice-gen.py" "./voices/es-CL.csv" es-CL-CatalinaNeural es_cl-catalina || exit 1
"./voice-gen.py" "./voices/es-ES.csv" es-ES-ElviraNeural es || exit 1
"./voice-gen.py" "./voices/fr-FR.csv" fr-FR-DeniseNeural fr || exit 1
"./voice-gen.py" "./voices/it-IT.csv" it-IT-ElsaNeural it || exit 1
"./voice-gen.py" "./voices/it-IT_scripts.csv" it-IT-ElsaNeural it/SCRIPTS || exit 1
"./voice-gen.py" "./voices/ja-JP.csv" ja-JP-NanamiNeural jp || exit 1
"./voice-gen.py" "./voices/ja-JP_scripts.csv" ja-JP-NanamiNeural jp/SCRIPTS || exit 1
"./voice-gen.py" "./voices/pt-PT.csv" pt-BR-FranciscaNeural pt || exit 1
"./voice-gen.py" "./voices/ru-RU.csv" ru-RU-SvetlanaNeural ru || exit 1
"./voice-gen.py" "./voices/sv-SE.csv" sv-SE-SofieNeural se --pitch "dn10%" --rate "dn0.9" || exit 1
"./voice-gen.py" "./voices/sv-SE_scripts.csv" sv-SE-SofieNeural se/SCRIPTS --pitch "dn10%" --rate "dn0.9" || exit 1
"./voice-gen.py" "./voices/uk-UA.csv" uk-UA-OstapNeural ua-ostap || exit 1
"./voice-gen.py" "./voices/uk-UA.csv" uk-UA-PolinaNeural ua-polina || exit 1
"./voice-gen.py" "./voices/zh-CN.csv" zh-CN-XiaoxiaoNeural cn || exit 1
"./voice-gen.py" "./voices/zh-TW.csv" zh-TW-HsiaoChenNeural tw || exit 1
"./voice-gen.py" "./voices/zh-HK.csv" zh-HK-HiuGaaiNeural hk --rate "dn1.2" || exit 1

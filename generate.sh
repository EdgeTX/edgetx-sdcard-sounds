#!/bin/bash

# delete logs from previous pass
find "$(dirname "$0")" -name "*.log" -delete

# include voice generator script
. "$(dirname "$0")/voice-gen.sh"

generate_lang voices/en-GB.csv en-IE-EmilyNeural en
generate_lang voices/en-GB.csv en-GB-LibbyNeural en_gb-libby
generate_lang voices/en-GB.csv en-GB-RyanNeural en_gb-ryan
generate_lang voices/en-US.csv en-US-SaraNeural en_us-sara
generate_lang voices/en-US.csv en-US-GuyNeural en_us-guy
generate_lang voices/pt-PT.csv pt-BR-FranciscaNeural pt
generate_lang voices/es-ES.csv es-ES-ElviraNeural es
generate_lang voices/es-CL-Catalina.csv es-CL-CatalinaNeural es_cl-catalina
generate_lang voices/it-IT.csv it-IT-ElsaNeural it
generate_lang voices/de-DE.csv de-DE-KatjaNeural de
generate_lang voices/fr-FR.csv fr-FR-DeniseNeural fr
generate_lang voices/ru-RU.csv ru-RU-SvetlanaNeural ru
generate_lang voices/cs-CZ.csv cs-CZ-VlastaNeural cz

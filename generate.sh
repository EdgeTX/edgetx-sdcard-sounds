#!/bin/bash

# delete logs from previous pass
find "$(dirname "$0")" -name "*.log" -delete

./voice-gen.py voices/cs-CZ.csv cs-CZ-VlastaNeural cz
./voice-gen.py voices/de-DE.csv de-DE-KatjaNeural de
./voice-gen.py voices/en-GB.csv en-IE-EmilyNeural en
./voice-gen.py voices/en-GB_scripts.csv en-IE-EmilyNeural en/SCRIPTS
./voice-gen.py voices/en-GB.csv en-GB-LibbyNeural en_gb-libby
./voice-gen.py voices/en-GB_scripts.csv en-GB-LibbyNeural en_gb-libby/SCRIPTS
./voice-gen.py voices/en-GB.csv en-GB-RyanNeural en_gb-ryan
./voice-gen.py voices/en-GB_scripts.csv en-GB-RyanNeural en_gb-ryan/SCRIPTS
./voice-gen.py voices/en-US.csv en-US-GuyNeural en_us-guy
./voice-gen.py voices/en-US_scripts.csv en-US-GuyNeural en_us-guy/SCRIPTS
./voice-gen.py voices/en-US.csv en-US-SaraNeural en_us-sara
./voice-gen.py voices/en-US_scripts.csv en-US-SaraNeural en_us-sara/SCRIPTS
./voice-gen.py voices/es-CL.csv es-CL-CatalinaNeural es_cl-catalina
./voice-gen.py voices/es-ES.csv es-ES-ElviraNeural es
./voice-gen.py voices/fr-FR.csv fr-FR-DeniseNeural fr
./voice-gen.py voices/it-IT.csv it-IT-ElsaNeural it
./voice-gen.py voices/ja-JP.csv ja-JP-NanamiNeural ja
./voice-gen.py voices/pt-PT.csv pt-BR-FranciscaNeural pt
./voice-gen.py voices/ru-RU.csv ru-RU-SvetlanaNeural ru
./voice-gen.py voices/sv-SE.csv sv-SE-SofieNeural sv
./voice-gen.py voices/sv-SE_scripts.csv sv-SE-SofieNeural sv/SCRIPTS
# ./voice-gen.py voices/zh-CN.csv

 

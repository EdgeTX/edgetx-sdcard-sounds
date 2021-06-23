#!/bin/bash

# include voice generator script
. $(dirname "$0")/voice-gen.sh

generate_lang voices/en-US.csv en-IE-EmilyNeural en
generate_lang voices/pt-PT.csv pt-BR-FranciscaNeural pt
generate_lang voices/es-ES.csv es-ES-ElviraNeural es
generate_lang voices/it-IT.csv it-IT-ElsaNeural it
generate_lang voices/de-DE.csv de-DE-KatjaNeural de
generate_lang voices/fr-FR.csv fr-FR-DeniseNeural fr
generate_lang voices/ru-RU.csv ru-RU-SvetlanaNeural ru
generate_lang voices/cs-CZ.csv cs-CZ-VlastaNeural cz
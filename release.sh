#!/bin/bash

: "${VERSION:=2.54}"
FFMPEG_FLAGS=(-hide_banner -loglevel error)
: "${FFMPEG_AF_FLAGS:=volume=6.0dB,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse}"

# delete release folder if already exists
[[ -e release ]] && rm -rf release

echo "VERSION         : ${VERSION}"
echo "FFMPEG_FLAGS    :" "${FFMPEG_FLAGS[@]}"
echo "FFMPEG_AF_FLAGS : ${FFMPEG_AF_FLAGS}"

echo "Creating release folders..."
find SOUNDS -type d -exec mkdir -p "release/{}" \;

NUM_OF_FILES=$(find SOUNDS -type f | wc -l)
echo "Normalizing $NUM_OF_FILES files..."
shopt -s globstar nullglob
for file in SOUNDS/**/*.wav; do
    [[ -e "$file" ]] || break  # handle the case of no *.wav files
    echo "$file"
    ffmpeg "${FFMPEG_FLAGS[@]}" -i "$file" -af "$FFMPEG_AF_FLAGS" "release/$file"
done

echo "Preparing release zip files..."
cd release || exit
for lang in SOUNDS/*/; do
    ZIPLANG=$(basename "$lang")
    [[ -e "$lang" ]] || break  # handle the case of no *.wav files
    echo Creating "edgetx-sdcard-sounds-$ZIPLANG-$VERSION.zip"
    find "$lang" -type f | zip -q -@ "edgetx-sdcard-sounds-$ZIPLANG-$VERSION.zip"
done

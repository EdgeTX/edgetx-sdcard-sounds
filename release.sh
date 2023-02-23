#!/bin/bash

: "${VERSION:=latest}"
FFMPEG_FLAGS=(-hide_banner -loglevel error)
: "${FFMPEG_AF_FLAGS:=silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse}"

# delete release folder if already exists
[[ -e release ]] && rm -rf release

echo "VERSION         : ${VERSION}"
echo "FFMPEG_FLAGS    :" "${FFMPEG_FLAGS[@]}"
echo "FFMPEG_AF_FLAGS : ${FFMPEG_AF_FLAGS}"

echo "Creating release folders..."
find SOUNDS -type d -exec mkdir -p "release/{}" \;

NUM_OF_FILES=$(find SOUNDS -type f | wc -l)
echo "Trim and normalize $NUM_OF_FILES files..."
shopt -s globstar nullglob
for file in SOUNDS/**/*.wav; do
    [[ -e "$file" ]] || break  # handle the case of no *.wav files
    echo "$file"
    ffmpeg "${FFMPEG_FLAGS[@]}" -i "$file" -af "$FFMPEG_AF_FLAGS" "release/$file"
    ffmpeg-normalize "release/$file" -o "release/$file" -f -nt peak -t 0
done

# Move processed files into variant folders
for dir in release/SOUNDS/*/; do
    if [ -d "$dir" ]; then
      dir=${dir%*/} 
      variant=$(basename "$dir")
      mkdir -p "release/${variant}/SOUNDS"
      mv "${dir}" "release/${variant}/SOUNDS"
    fi
done

# Trim release folder names to expected two characters
for dir in release/**/SOUNDS/*/; do
    if [ -d "$dir" ]; then
      dir=${dir%*/} 
      variant=$(basename "$dir")
      twoLetterVariant=${variant:0:2}
      if [[ "${variant}" != "${twoLetterVariant}" ]]; then
        echo "${variant} => ${twoLetterVariant}"
        mv "release/${variant}/SOUNDS/${variant}" "release/${variant}/SOUNDS/${twoLetterVariant}"
      fi
    fi
done

# Remove leftover parent SOUNDS directory
if [ -d release/SOUNDS ]; then
  rmdir "release/SOUNDS"
fi

echo "Preparing release zip files..."
WORKDIR=$(pwd)
for d in release/*/ ; do
    cd "$WORKDIR/${d}" || exit
    for lang in SOUNDS/*/ ; do
        ZIPLANG=$(basename "$d")
        [[ -e "$lang" ]] || break  # handle the case of no *.wav files
        echo Creating "edgetx-sdcard-sounds-$ZIPLANG-$VERSION.zip"
        find "$lang" -type f | zip -q -@ "$WORKDIR/release/edgetx-sdcard-sounds-$ZIPLANG-$VERSION.zip"
    done
    cd "$WORKDIR/release" || exit
done

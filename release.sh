#!/bin/bash

version=2.4.0-rc3

# make normalized folders
find SOUNDS -type d | xargs -I % mkdir -p normalized/%

# normalize each file and replace source
for file in $(find SOUNDS -type f)
do
    ffmpeg -i $file -af "volume=4.5dB,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB,areverse" normalized/$file && \
    mv -f normalized/$file $file
done

# compress the release files
for lang in $(ls SOUNDS)
do
    find SOUNDS/$lang -type f | zip -@ edgetx-sdcard-sounds-$lang-$version.zip
done

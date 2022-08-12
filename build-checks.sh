#!/bin/bash
shopt -s globstar nullglob

echo "File name length checks..."

for file in SOUNDS/**/*.wav
do 
    filename=$(basename "$file")
    filename="${filename%.*}"
    # extension="${filename##*.}"
    dir=$(dirname "$file")
    dir=$(basename "$dir")

    if [ "$dir" == "YAAPU" ] || [ "$dir" == "INAV" ] ||
       [ "$dir" == "BETAFLIGHT" ]; then
        continue
    fi

    if [ "$dir" != "SYSTEM" ]; then
        if (( ${#filename} > 6 )); then
            echo "Filename is too long: $file"
            continue
        fi
    else
        if (( ${#filename} > 8 )); then
            echo "Filename is too long: $file"
            continue
        fi
    fi
done

#!/bin/bash

generate_lang () {
  # $1: CSV file
  # $2: voice name
  # $3: language directory

  HEADER_DONE=0
  ROOT=SOUNDS
  DELAY=3
  CSV_FILE=$1
  VOICE_NAME=$2
  LANG=$3

  LINE_NUMBER=0
  NUM_OF_LINES=$(wc -l < "$CSV_FILE")
  NUM_OF_LINES=$((NUM_OF_LINES-1))

  echo "Generating $VOICE_NAME ($LANG)... $NUM_OF_LINES lines"

  while read -r line
  do
    # consume header line
    if [ "$HEADER_DONE" -ne 1 ]; then
        HEADER_DONE=1
        continue
    fi

    LINE_NUMBER=$((LINE_NUMBER+1))

    SUBDIR=$(echo -n "$line" | awk -F ';' '{print $1}')
    FILENAME=$(echo -n "$line" | awk -F ';' '{print $2}')
    TEXT=$(echo -n "$line" | awk -F ';' '{print $3}')

    if [ "$SUBDIR" != "" ]; then
      OUTDIR="$ROOT/$LANG/$SUBDIR"
    else
      OUTDIR="$ROOT/$LANG"
    fi

    [ ! -d "$OUTDIR" ]  && mkdir -p "$OUTDIR"

    if test -f "$OUTDIR/$FILENAME"; then
      echo "($LINE_NUMBER/$NUM_OF_LINES) File '$OUTDIR/$FILENAME' already exists. Skipping."
    else
      echo "($LINE_NUMBER/$NUM_OF_LINES) File '$OUTDIR/$FILENAME' does not exist. Creating... "
      spx synthesize --text \""$TEXT"\" --voice "$VOICE_NAME" --audio output "$OUTDIR/$FILENAME" || break
      sleep $DELAY
    fi
  done < "$CSV_FILE"
}

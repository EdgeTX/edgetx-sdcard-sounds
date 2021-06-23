#!/bin/bash

generate_lang () {
  while read line
  do
      destination=`echo -n $line | awk -F ';' '{print $1}'`
      filename=`echo -n $line | awk -F ';' '{print $2}'`
      text=`echo -n $line | awk -F ';' '{print $3}'`
      if test -f $destination/$filename; then
          echo "File $filename already exists. Skipping."
      else
          echo "File $filename does not exists. Creating."
          spx synthesize --text \""$text"\" --voice $2 --audio output $destination/$filename
      fi
  done < $1
}

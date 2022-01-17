# EdgeTX - Sound packs

This is a new workflow to create EdgeTX (and untested OpenTX) Soundpackages and custom sounds for your Radio. This repository used the free google Text to speach API from google Translate.

You can use the Custom Sound Generator to create your own soundfiles with the same voice.

In order to create a complete language Pack you can submit a new CSV File as a pull request to this repository. Please follow the following standard for creating the CSV.

 

## CSV File Name labeling:

  
**aa-BB-c-Dddd.csv**

**aa** = 2 small letters for languge

Followed by „-“

**BB** = 2 capital letter country code in [Alpha 2-code](https://www.iban.com/country-codes) 

Followed by „-“

**c** = m for male and f for femal

_if applicable:_ Followed by „-“

**Dddd** = Name of language Starting with a capital Letter.

  
Example:

de-DE-m.csv for German language and German accent with a male voice.

de-AT-f-Gabi.csv for German language and Austrian accent with a female voice named Gabi.

en-GB-m-Ryan.csv for English langauge and British accent with a male voice named Ryan.

  

  

## CSV File Layout:

  

The CSV file needs to have a semicolon as a seperator between each field. It needs to have the following 7 fields:

  

Example SOUNDS/it-IT-f/SYSTEM;0010.wav;10;it;IT

SOUNDS/en-GB-m/SYSTEM/;0010.wav;10;en;GB;m;Ryan

  

Field 1:

File location on SD Card.

Subfolder SOUNDS/ langauge in small letters „-“ followed by gender followed by „-“ followed by country code in Alpha 2 letter Capital followed „-“ followed by Name of voice with starting with capital Letter + if applicable: subfolder SYSTEMS

  

Field 2:

Filename ( No longer than 6 Characters + .wav)

Field 3:

Spoken Text

Field 4:

Lanuage in small letters

Field 5:

Accent in [Alpha 2-code](https://www.iban.com/country-codes)  as Capital letters

Field 6:

Gender of voice either m or f

Field 7:

Name of voice with starting with Capital letter.


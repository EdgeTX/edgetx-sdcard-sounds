#!/bin/bash

# Build and install OpenSSL 1.1.1u
wget -O - https://www.openssl.org/source/openssl-1.1.1u.tar.gz | tar zxf -
cd openssl-1.1.1u
./config --prefix=/usr/local
make -j $(nproc)
sudo make install_sw install_ssldirs
sudo ldconfig
cd .. && sudo rm -R openssl-1.1.1u

# Install .NET 6.0 SDK and the Speech CLI tool
sudo apt-get update && sudo apt-get install -y dotnet-sdk-6.0
dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI --version 1.42.0

# Install the Azure Speech SDK for Python
python -m pip install azure-cognitiveservices-speech ffmpeg-normalize

# Install ffmpeg for GLaDOS post-processing and release generation
sudo apt-get install -y ffmpeg
python -m pip install ffmpeg-normalize

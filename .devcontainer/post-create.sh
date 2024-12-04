#!/bin/bash

# Install required packages
sudo apt-get update
sudo apt-get install -y build-essential ca-certificates libasound2-dev libssl-dev python3 python3-pip python3-venv python-is-python3 dotnet-sdk-8.0 ffmpeg

# Install Azure Speech CLI tool
dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI

# Activate virtual environment
python3 -m venv .venv

# Install the Azure Speech SDK for Python
.venv/bin/pip install azure-cognitiveservices-speech

# Activate the virtual environment
source .venv/bin/activate
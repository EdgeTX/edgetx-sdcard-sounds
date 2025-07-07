#!/bin/bash

# Install required packages
echo "Installing required packages..."
sudo apt-get update &> /dev/null && sudo apt-get install --no-install-recommends -y python3 python-is-python3 dotnet-sdk-8.0 ffmpeg

# Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install Azure Speech CLI tool
echo "Installing Azure Speech CLI tool..."
dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI --version 1.44.0

# Install Python dependencies with uv
echo "Installing Python dependencies with uv..."
uv sync

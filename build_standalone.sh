#!/bin/bash

set -e

echo "Building Kokoro TTS standalone executable for Linux..."

export TMPDIR=/home/ubuntu/kokoro_tmp
mkdir -p $TMPDIR

pip install -e .

mkdir -p build

echo "Downloading model files..."
python docker/scripts/download_model.py --output api/src/models/v1_0

echo "Building with PyInstaller..."
pyinstaller --clean kokoro_tts.spec

echo "Copying distribution files..."
rm -rf build/kokoro-tts
cp -r dist/kokoro-tts build/

echo "Copying model file..."
mkdir -p build/kokoro-tts/api/src/models/v1_0
cp api/src/models/v1_0/kokoro-v1_0.pth build/kokoro-tts/api/src/models/v1_0/

echo "Build completed successfully!"
echo "The standalone distribution is available at ./build/kokoro-tts/"
echo "To run the server, execute: ./build/kokoro-tts/kokoro-tts"
echo "The server will be available at http://localhost:8880"

#!/bin/bash

set -e

echo "Building Kokoro TTS standalone executable for Linux..."

export TMPDIR=/home/ubuntu/kokoro_tmp
mkdir -p $TMPDIR

pip install -e .

mkdir -p build

python docker/scripts/download_model.py --output api/src/models/v1_0

pyinstaller --clean kokoro_tts.spec

cp dist/kokoro-tts build/

echo "Build completed successfully!"
echo "The standalone executable is available at ./build/kokoro-tts"
echo "To run the server, execute: ./build/kokoro-tts"
echo "The server will be available at http://localhost:8880"

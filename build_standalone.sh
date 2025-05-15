#!/bin/bash

set -e

echo "Building Kokoro TTS standalone executable..."

mkdir -p build
cd build

echo "Running PyOxidizer build..."
cd ../pyoxidizer.bzl
pyoxidizer build --release

echo "Copying executable to build directory..."
cp build/*/release/install/kokoro-tts ../build/

cd ../build
mkdir -p models/v1_0
mkdir -p voices/v1_0
mkdir -p web

echo "Downloading model files..."
python ../docker/scripts/download_model.py --output models/v1_0

echo "Copying voice files..."
cp -r ../api/src/voices/v1_0/* voices/v1_0/

echo "Copying web files..."
cp -r ../web/* web/

echo "Build completed successfully!"
echo "The standalone executable is available at ./build/kokoro-tts"
echo "To run the server, execute: ./build/kokoro-tts"
echo "The server will be available at http://localhost:8880"

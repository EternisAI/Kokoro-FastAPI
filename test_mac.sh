#!/bin/bash

set -e

echo "Testing Kokoro TTS standalone executable for Mac ARM64 with GPU support..."

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script must be run on macOS."
    exit 1
fi

if [ ! -f ./build_mac/kokoro-tts-gpu ]; then
    echo "Error: Executable not found. Please run build_mac.sh first."
    exit 1
fi

echo "Starting the server..."
./build_mac/kokoro-tts-gpu > server.log 2>&1 &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 5

echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8880/health)
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "Health check successful!"
else
    echo "Health check failed. Response: $HEALTH_RESPONSE"
    kill $SERVER_PID
    exit 1
fi

echo "Testing TTS functionality..."
curl -s -X POST "http://localhost:8880/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{"model": "kokoro", "voice": "af_bella", "input": "Hello world!", "response_format": "mp3"}' \
  --output test.mp3

if [ -f test.mp3 ] && [ $(stat -f%z test.mp3) -gt 0 ]; then
    echo "TTS test successful! Audio file generated."
else
    echo "TTS test failed. Audio file not generated or empty."
    kill $SERVER_PID
    exit 1
fi

echo "Stopping the server..."
kill $SERVER_PID

echo "All tests passed successfully!"

#!/bin/bash

set -e

echo "Testing Kokoro TTS standalone executable..."

if [ ! -d ./build/kokoro-tts ]; then
    echo "Error: Distribution directory not found. Please run build_standalone.sh first."
    exit 1
fi

if [ ! -f ./build/kokoro-tts/kokoro-tts ]; then
    echo "Error: Executable not found in distribution directory. Please run build_standalone.sh first."
    exit 1
fi

echo "Starting the server..."
cd ./build/kokoro-tts
./kokoro-tts > ../../server.log 2>&1 &
SERVER_PID=$!
cd ../..

echo "Waiting for server to start (this may take up to 60 seconds)..."
MAX_WAIT=60
WAIT_COUNT=0
SERVER_READY=false

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8880/health > /dev/null 2>&1; then
        SERVER_READY=true
        break
    fi
    sleep 5
    WAIT_COUNT=$((WAIT_COUNT + 5))
    echo "Still waiting... ($WAIT_COUNT seconds)"
done

if [ "$SERVER_READY" = false ]; then
    echo "Server did not start within $MAX_WAIT seconds. Check server.log for errors."
    kill $SERVER_PID
    exit 1
fi

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

if [ -f test.mp3 ] && [ $(stat -c%s test.mp3) -gt 0 ]; then
    echo "TTS test successful! Audio file generated."
else
    echo "TTS test failed. Audio file not generated or empty."
    kill $SERVER_PID
    exit 1
fi

echo "Stopping the server..."
kill $SERVER_PID

echo "All tests passed successfully!"

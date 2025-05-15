#!/bin/bash

set -e

echo "Creating Kokoro TTS distribution package..."

if [ ! -d ./build ]; then
    echo "Error: Build directory not found. Please run build_standalone.sh first."
    exit 1
fi

DIST_DIR="kokoro-tts-standalone"
rm -rf $DIST_DIR
mkdir -p $DIST_DIR

cp build/kokoro-tts $DIST_DIR/
cp -r build/models $DIST_DIR/
cp -r build/voices $DIST_DIR/
cp -r build/web $DIST_DIR/

cat > $DIST_DIR/README.txt << 'EOF'
Kokoro TTS Standalone Server
===========================

This is a standalone executable for the Kokoro TTS server.

Usage:
1. Run the executable: ./kokoro-tts
2. The server will be available at http://localhost:8880
3. API Documentation: http://localhost:8880/docs
4. Web Interface: http://localhost:8880/web

Example curl command:
curl -X POST "http://localhost:8880/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{"model": "kokoro", "voice": "af_bella", "input": "Hello world!", "response_format": "mp3"}' \
  --output test.mp3

For more information, visit: https://github.com/EternisAI/Kokoro-FastAPI
EOF

echo "Creating ZIP archive..."
zip -r kokoro-tts-standalone.zip $DIST_DIR

echo "Distribution package created: kokoro-tts-standalone.zip"

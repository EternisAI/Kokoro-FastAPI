#!/bin/bash

set -e

echo "Creating Kokoro TTS distribution packages..."

if [ -d ./build ]; then
    echo "Creating Linux distribution package..."
    LINUX_DIST_DIR="kokoro-tts-standalone-linux"
    rm -rf $LINUX_DIST_DIR
    mkdir -p $LINUX_DIST_DIR

    cp build/kokoro-tts $LINUX_DIST_DIR/
    
    cat > $LINUX_DIST_DIR/README.txt << 'EOF'
Kokoro TTS Standalone Server (Linux)
===================================

This is a standalone executable for the Kokoro TTS server on Linux.

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

    echo "Creating Linux ZIP archive..."
    zip -r kokoro-tts-standalone-linux.zip $LINUX_DIST_DIR
    echo "Linux distribution package created: kokoro-tts-standalone-linux.zip"
fi

if [ -d ./build_mac ]; then
    echo "Creating Mac ARM64 distribution package..."
    MAC_DIST_DIR="kokoro-tts-standalone-mac"
    rm -rf $MAC_DIST_DIR
    mkdir -p $MAC_DIST_DIR

    cp build_mac/kokoro-tts-gpu $MAC_DIST_DIR/
    
    cat > $MAC_DIST_DIR/README.txt << 'EOF'
Kokoro TTS Standalone Server (Mac ARM64 with GPU Support)
======================================================

This is a standalone executable for the Kokoro TTS server on Mac ARM64 with GPU support.

Usage:
1. Run the executable: ./kokoro-tts-gpu
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

    echo "Creating Mac ZIP archive..."
    zip -r kokoro-tts-standalone-mac.zip $MAC_DIST_DIR
    echo "Mac distribution package created: kokoro-tts-standalone-mac.zip"
fi

echo "Distribution packages created successfully."

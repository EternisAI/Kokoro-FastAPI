#!/usr/bin/env python3
"""Entry point for PyInstaller-packaged Kokoro TTS server."""

import os
import sys
import uvicorn

os.environ["MODEL_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "src", "models", "v1_0")
os.environ["VOICES_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "src", "voices", "v1_0")
os.environ["WEB_PLAYER_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
os.environ["USE_GPU"] = "false"
os.environ["USE_ONNX"] = "false"

if __name__ == "__main__":
    uvicorn.run("api.src.main:app", host="0.0.0.0", port=8880)

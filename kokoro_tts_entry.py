#!/usr/bin/env python3
"""Entry point for PyInstaller-packaged Kokoro TTS server."""

import os
import sys
import uvicorn
import shutil

if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(sys.executable))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

print(f"Base path: {base_path}")
print(f"Current working directory: {os.getcwd()}")

if getattr(sys, 'frozen', False) and not hasattr(sys, '_MEIPASS'):
    app_dir = os.path.dirname(os.path.abspath(sys.executable))
    os.environ["MODEL_DIR"] = os.path.join(app_dir, "api", "src", "models", "v1_0")
    os.environ["VOICES_DIR"] = os.path.join(app_dir, "api", "src", "voices", "v1_0")
    os.environ["WEB_PLAYER_PATH"] = os.path.join(app_dir, "web")
    os.environ["PYTHONPATH"] = app_dir
else:
    os.environ["MODEL_DIR"] = os.path.join(base_path, "api", "src", "models", "v1_0")
    os.environ["VOICES_DIR"] = os.path.join(base_path, "api", "src", "voices", "v1_0")
    os.environ["WEB_PLAYER_PATH"] = os.path.join(base_path, "web")
    os.environ["PYTHONPATH"] = base_path

os.environ["USE_GPU"] = "false"
os.environ["USE_ONNX"] = "false"

if os.path.exists("/usr/lib/x86_64-linux-gnu/espeak-ng-data"):
    os.environ["ESPEAK_DATA_PATH"] = "/usr/lib/x86_64-linux-gnu/espeak-ng-data"
elif os.path.exists("/usr/share/espeak-ng-data"):
    os.environ["ESPEAK_DATA_PATH"] = "/usr/share/espeak-ng-data"

print(f"MODEL_DIR: {os.environ['MODEL_DIR']}")
print(f"VOICES_DIR: {os.environ['VOICES_DIR']}")
print(f"WEB_PLAYER_PATH: {os.environ['WEB_PLAYER_PATH']}")
if "ESPEAK_DATA_PATH" in os.environ:
    print(f"ESPEAK_DATA_PATH: {os.environ['ESPEAK_DATA_PATH']}")

if __name__ == "__main__":
    print("Starting Kokoro TTS server...")
    uvicorn.run("api.src.main:app", host="0.0.0.0", port=8880)

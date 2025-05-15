#!/usr/bin/env python3
"""Entry point for PyInstaller-packaged Kokoro TTS server."""

import os
import sys
import uvicorn
import shutil
import importlib.util
import importlib.machinery
import json
import inspect
import types
import warnings

original_getsource = inspect.getsource
original_getsourcelines = inspect.getsourcelines
original_findsource = inspect.findsource

def patched_getsource(object):
    try:
        return original_getsource(object)
    except Exception:
        if isinstance(object, types.FunctionType):
            return f"def {object.__name__}(*args, **kwargs): pass"
        elif isinstance(object, type):
            return f"class {object.__name__}: pass"
        return ""

def patched_getsourcelines(object):
    try:
        return original_getsourcelines(object)
    except Exception:
        if isinstance(object, types.FunctionType):
            return ([f"def {object.__name__}(*args, **kwargs): pass"], 0)
        elif isinstance(object, type):
            return ([f"class {object.__name__}: pass"], 0)
        return ([""], 0)

def patched_findsource(object):
    try:
        return original_findsource(object)
    except Exception:
        return ([""], 0)

inspect.getsource = patched_getsource
inspect.getsourcelines = patched_getsourcelines
inspect.findsource = patched_findsource

warnings.filterwarnings("ignore", "Couldn't find ffmpeg or avconv")

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

espeak_data_paths = [
    "/usr/lib/x86_64-linux-gnu/espeak-ng-data",
    "/usr/share/espeak-ng-data",
    "/usr/local/share/espeak-ng-data",
    "/opt/homebrew/share/espeak-ng-data",  # For Mac
    os.path.join(base_path, "espeak-ng-data")  # Bundled with executable
]

espeak_data_found = False
for path in espeak_data_paths:
    if os.path.exists(path) and os.path.isdir(path):
        os.environ["ESPEAK_DATA_PATH"] = path
        espeak_data_found = True
        break

if not espeak_data_found:
    mock_espeak_dir = os.path.join(base_path, "espeakng_loader", "espeak-ng-data")
    os.makedirs(mock_espeak_dir, exist_ok=True)
    
    with open(os.path.join(mock_espeak_dir, "intonation"), "w") as f:
        f.write("")
    
    with open(os.path.join(mock_espeak_dir, "phondata"), "w") as f:
        f.write("")
    
    with open(os.path.join(mock_espeak_dir, "phonindex"), "w") as f:
        f.write("")
    
    with open(os.path.join(mock_espeak_dir, "phontab"), "w") as f:
        f.write("")
    
    os.environ["ESPEAK_DATA_PATH"] = mock_espeak_dir

try:
    lang_tags_dir = os.path.join(base_path, "language_tags", "data", "json")
    os.makedirs(lang_tags_dir, exist_ok=True)
    
    index_path = os.path.join(lang_tags_dir, "index.json")
    if not os.path.exists(index_path) or os.path.isdir(index_path):
        with open(index_path, "w") as f:
            json.dump({"language": "index.json", "extlang": "extlang.json", "script": "script.json", 
                      "region": "region.json", "variant": "variant.json", "grandfathered": "grandfathered.json", 
                      "redundant": "redundant.json"}, f)
    
    for filename in ["extlang.json", "script.json", "region.json", "variant.json", "grandfathered.json", "redundant.json"]:
        file_path = os.path.join(lang_tags_dir, filename)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            with open(file_path, "w") as f:
                json.dump({}, f)
except Exception as e:
    print(f"Warning: Failed to create language_tags data: {e}")

try:
    import subprocess
    subprocess.run(["which", "ffmpeg"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("ffmpeg found")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("ffmpeg not found. Audio conversion may not work properly.")
    os.environ["FFMPEG_MISSING"] = "true"

print(f"MODEL_DIR: {os.environ['MODEL_DIR']}")
print(f"VOICES_DIR: {os.environ['VOICES_DIR']}")
print(f"WEB_PLAYER_PATH: {os.environ['WEB_PLAYER_PATH']}")
print(f"ESPEAK_DATA_PATH: {os.environ['ESPEAK_DATA_PATH']}")

if __name__ == "__main__":
    print("Starting Kokoro TTS server...")
    uvicorn.run("api.src.main:app", host="0.0.0.0", port=8880)

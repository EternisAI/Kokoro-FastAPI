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
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kokoro_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("kokoro_tts")

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
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")

def exception_handler(exc_type, exc_value, exc_traceback):
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = exception_handler

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

def list_directory_contents(path):
    """List all files and directories at the given path."""
    logger.debug(f"Listing contents of directory: {path}")
    try:
        if os.path.exists(path) and os.path.isdir(path):
            contents = os.listdir(path)
            for item in contents:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    logger.debug(f"  DIR: {item}")
                else:
                    logger.debug(f"  FILE: {item} ({os.path.getsize(item_path)} bytes)")
        else:
            logger.warning(f"Path does not exist or is not a directory: {path}")
    except Exception as e:
        logger.error(f"Error listing directory contents: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting Kokoro TTS server...")
        
        logger.debug("Environment variables:")
        for key, value in os.environ.items():
            if key in ["MODEL_DIR", "VOICES_DIR", "WEB_PLAYER_PATH", "ESPEAK_DATA_PATH", "USE_GPU", "USE_ONNX"]:
                logger.debug(f"  {key}={value}")
        
        model_dir = os.environ.get("MODEL_DIR")
        if model_dir:
            list_directory_contents(model_dir)
            list_directory_contents(os.path.join(model_dir, "v1_0"))
        
        voices_dir = os.environ.get("VOICES_DIR")
        if voices_dir:
            list_directory_contents(voices_dir)
        
        logger.info("Starting uvicorn server...")
        uvicorn.run("api.src.main:app", host="0.0.0.0", port=8880)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

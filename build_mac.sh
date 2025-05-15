#!/bin/bash

set -e

echo "Building Kokoro TTS standalone executable for Mac ARM64 with GPU support..."

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script must be run on macOS."
    exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
    echo "Warning: This script is designed for Apple Silicon (ARM64) Macs."
    echo "Press Enter to continue anyway, or Ctrl+C to cancel."
    read
fi

export TMPDIR=~/kokoro_tmp
mkdir -p $TMPDIR

pip install -e .

mkdir -p build_mac

python docker/scripts/download_model.py --output api/src/models/v1_0

cat > kokoro_tts_mac_entry.py << 'EOF'
#!/usr/bin/env python3
"""Entry point for PyInstaller-packaged Kokoro TTS server with GPU support for Mac."""

import os
import sys
import uvicorn

os.environ["MODEL_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "src", "models", "v1_0")
os.environ["VOICES_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "src", "voices", "v1_0")
os.environ["WEB_PLAYER_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
os.environ["USE_GPU"] = "true"
os.environ["USE_ONNX"] = "false"
os.environ["DEVICE_TYPE"] = "mps"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

if __name__ == "__main__":
    uvicorn.run("api.src.main:app", host="0.0.0.0", port=8880)
EOF

cat > kokoro_tts_mac.spec << 'EOF'

import os
from pathlib import Path

block_cipher = None

project_root = os.path.abspath(os.path.dirname(__file__))

model_dir = os.path.join(project_root, 'api', 'src', 'models', 'v1_0')
voices_dir = os.path.join(project_root, 'api', 'src', 'voices', 'v1_0')
web_dir = os.path.join(project_root, 'web')

os.makedirs(model_dir, exist_ok=True)
os.makedirs(voices_dir, exist_ok=True)

model_file = os.path.join(model_dir, 'kokoro-v1_0.pth')
config_file = os.path.join(model_dir, 'config.json')

if not os.path.exists(model_file) or not os.path.exists(config_file):
    print("Downloading model files...")
    from docker.scripts.download_model import download_model
    download_model(model_dir)

voice_files = []
for file in os.listdir(voices_dir):
    if file.endswith('.pt'):
        voice_files.append((os.path.join(voices_dir, file), os.path.join('api', 'src', 'voices', 'v1_0', file)))

web_files = []
for root, dirs, files in os.walk(web_dir):
    for file in files:
        source_path = os.path.join(root, file)
        relative_path = os.path.relpath(source_path, project_root)
        web_files.append((source_path, relative_path))

a = Analysis(
    ['kokoro_tts_mac_entry.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (model_file, os.path.join('api', 'src', 'models', 'v1_0')),
        (config_file, os.path.join('api', 'src', 'models', 'v1_0')),
    ] + voice_files + web_files,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.http.auto',
        'api.src.main',
        'api.src.core.config',
        'api.src.core.paths',
        'api.src.inference.model_manager',
        'api.src.inference.voice_manager',
        'api.src.inference.kokoro_v1',
        'api.src.routers.debug',
        'api.src.routers.development',
        'api.src.routers.openai_compatible',
        'api.src.routers.web_player',
        'api.src.services.temp_manager',
        'kokoro',
        'misaki',
        'misaki.en',
        'misaki.ja',
        'misaki.ko',
        'misaki.zh',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='kokoro-tts-gpu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

pyinstaller --clean kokoro_tts_mac.spec

cp dist/kokoro-tts-gpu build_mac/

echo "Build completed successfully!"
echo "The standalone executable is available at ./build_mac/kokoro-tts-gpu"
echo "To run the server, execute: ./build_mac/kokoro-tts-gpu"
echo "The server will be available at http://localhost:8880"

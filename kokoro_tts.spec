# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = os.path.abspath(os.path.dirname(__file__))

# Define paths for model and voice files
model_dir = os.path.join(project_root, 'api', 'src', 'models', 'v1_0')
voices_dir = os.path.join(project_root, 'api', 'src', 'voices', 'v1_0')
web_dir = os.path.join(project_root, 'web')

# Create directories if they don't exist
os.makedirs(model_dir, exist_ok=True)
os.makedirs(voices_dir, exist_ok=True)

# Download model files if they don't exist
model_file = os.path.join(model_dir, 'kokoro-v1_0.pth')
config_file = os.path.join(model_dir, 'config.json')

if not os.path.exists(model_file) or not os.path.exists(config_file):
    print("Downloading model files...")
    from docker.scripts.download_model import download_model
    download_model(model_dir)

# Collect all voice files
voice_files = []
for file in os.listdir(voices_dir):
    if file.endswith('.pt'):
        voice_files.append((os.path.join(voices_dir, file), os.path.join('api', 'src', 'voices', 'v1_0', file)))

# Collect all web files
web_files = []
for root, dirs, files in os.walk(web_dir):
    for file in files:
        source_path = os.path.join(root, file)
        relative_path = os.path.relpath(source_path, project_root)
        web_files.append((source_path, relative_path))

a = Analysis(
    ['kokoro_tts_entry.py'],
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
    name='kokoro-tts',
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

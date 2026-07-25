# -*- mode: python ; coding: utf-8 -*-

import os
import mediapipe

# Find the mediapipe package directory
mediapipe_dir = os.path.dirname(mediapipe.__file__)

# Collect ALL mediapipe data files (models, graphs, label files, etc.)
# Must include: .tflite (models), .binarypb (graphs), .txt (handedness labels), .fbs (flatbuffers)
# Without handedness.txt, multi_handedness is broken in bundled apps.
MEDIAPIPE_DATA_EXTENSIONS = {'.tflite', '.binarypb', '.pbtxt', '.pb', '.txt', '.fbs'}

mediapipe_datas = []
for root, dirs, files in os.walk(mediapipe_dir):
    # Skip Python cache directories
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in MEDIAPIPE_DATA_EXTENSIONS:
            full_path = os.path.join(root, file)
            # Preserve the relative path structure inside the mediapipe package
            # root_path in solution_base.py = _MEIPASS (3 levels up from solution_base.pyc)
            # solution_base.py is at: _MEIPASS/mediapipe/python/solution_base.pyc
            # So rel_dir must be relative to site-packages (os.path.dirname(mediapipe_dir))
            rel_dir = os.path.relpath(root, os.path.dirname(mediapipe_dir))
            mediapipe_datas.append((full_path, rel_dir))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=mediapipe_datas,
    hiddenimports=[
        'mediapipe',
        'mediapipe.python',
        'mediapipe.python.solutions',
        'mediapipe.python.solutions.hands',
        'mediapipe.python.solution_base',
        'mediapipe.python._framework_bindings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SnakeGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SnakeGame',
)

app = BUNDLE(
    coll,
    name='SnakeGame.app',
    bundle_identifier='com.mizhabas.snakegame',
    info_plist={
        'NSCameraUsageDescription': 'This game requires camera access for hand gesture control.',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
    },
)

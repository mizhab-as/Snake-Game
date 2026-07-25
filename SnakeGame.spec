# -*- mode: python ; coding: utf-8 -*-

import os
import mediapipe

# Find the mediapipe package directory
mediapipe_dir = os.path.dirname(mediapipe.__file__)

# Collect all mediapipe data files (models, graphs, etc.)
mediapipe_datas = []
for root, dirs, files in os.walk(mediapipe_dir):
    for file in files:
        if file.endswith(('.tflite', '.binarypb', '.pbtxt', '.pb')):
            full_path = os.path.join(root, file)
            # Preserve the relative path structure inside the mediapipe package
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

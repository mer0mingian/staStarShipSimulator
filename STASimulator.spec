# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for STA Starship Simulator Mac app."""

import os
import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)

# Get version from sta/version.py
sys.path.insert(0, str(project_root))
from sta.version import __version__

# Collect all data files
datas = [
    # Templates
    (str(project_root / 'sta' / 'web' / 'templates'), 'sta/web/templates'),
    # Static files (CSS, JS, fonts, audio)
    (str(project_root / 'sta' / 'web' / 'static'), 'sta/web/static'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'sta',
    'sta.web',
    'sta.web.app',
    'sta.web.routes',
    'sta.web.routes.main',
    'sta.web.routes.encounters',
    'sta.web.routes.api',
    'sta.web.routes.campaigns',
    'sta.database',
    'sta.database.db',
    'sta.database.schema',
    'sta.models',
    'sta.models.character',
    'sta.models.starship',
    'sta.models.combat',
    'sta.models.enums',
    'sta.mechanics',
    'sta.mechanics.dice',
    'sta.mechanics.actions',
    'sta.mechanics.action_config',
    'sta.mechanics.action_handlers',
    'sta.mechanics.movement',
    'sta.generators',
    'sta.generators.character',
    'sta.generators.starship',
    'sta.generators.data',
    'sta.version',
    'sta.updater',
    'flask',
    'werkzeug',
    'werkzeug.serving',
    'jinja2',
    'sqlalchemy',
    'sqlalchemy.sql.default_comparator',
]

a = Analysis(
    ['launcher.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'tests',
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='STASimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=True,  # Important for macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='STASimulator',
)

app = BUNDLE(
    coll,
    name='STA Starship Simulator.app',
    icon='AppIcon.icns',
    bundle_identifier='com.tommertron.sta-simulator',
    info_plist={
        'CFBundleName': 'STA Starship Simulator',
        'CFBundleDisplayName': 'STA Starship Simulator',
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
)

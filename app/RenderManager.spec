# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for RenderManager.app
Build from the app/ directory:
    pyinstaller RenderManager.spec --clean
"""

from pathlib import Path

SPEC_DIR  = Path(SPECPATH)          # .../app/
ROOT      = SPEC_DIR.parent          # .../Blender-Render-Util/
SERVER    = ROOT / 'server'
DIST_DIR  = SERVER / 'frontend' / 'dist'

a = Analysis(
    [str(SPEC_DIR / 'launcher.py')],
    pathex=[str(SERVER)],
    binaries=[],
    datas=[
        # Pre-built React frontend
        (str(DIST_DIR),                       'frontend/dist'),
        # Server source files
        (str(SERVER / 'app.py'),              '.'),
        (str(SERVER / 'monitor.py'),          '.'),
        (str(SERVER / 'config_manager.py'),   '.'),
        # Config template for first-run
        (str(SERVER / 'config.template.json'), '.'),
        # Render script
        (str(ROOT / 'batchedFrame_render.sh'), '.'),
    ],
    hiddenimports=[
        # uvicorn internals
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # FastAPI / Starlette
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.middleware.cors',
        'starlette',
        'starlette.staticfiles',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.routing',
        'anyio',
        'anyio._backends._asyncio',
        'h11',
        # WebSockets
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        # PyWebView macOS backend
        'webview',
        'webview.platforms.cocoa',
        # Watchdog macOS backend
        'watchdog',
        'watchdog.observers',
        'watchdog.observers.fsevents',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RenderManager',
    debug=False,
    strip=False,
    upx=False,
    console=False,      # No terminal window
    windowed=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='RenderManager',
)

app = BUNDLE(
    coll,
    name='RenderManager.app',
    icon=None,          # Phase 3 placeholder — add .icns before release
    bundle_identifier='com.renderutil.rendermanager',
    info_plist={
        'CFBundleName':              'Render Manager',
        'CFBundleDisplayName':       'Render Manager',
        'CFBundleShortVersionString': '5.2.1',
        'CFBundleVersion':           '5.2.1',
        'NSHighResolutionCapable':   True,
        'NSRequiresAquaSystemAppearance': False,  # Supports dark mode
    },
)

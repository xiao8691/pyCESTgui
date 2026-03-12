# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['E:\\01_CEST\\pyCESTgui'],
    binaries=[],
    datas=[('E:\\01_CEST\\pyCESTgui\\.venv\\Lib\\site-packages\\PyQt5', 'PyQt5')],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip', 'matplotlib.backends.backend_qt5agg', 'scipy', 'scipy.optimize', 'scipy.interpolate', 'scipy.ndimage', 'sklearn', 'sklearn.decomposition', 'sklearn.metrics'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'wx', 'PySide2', 'PySide6', 'PyQt6', 'matplotlib.tests', 'nibabel.tests', 'numpy.tests', 'scipy.tests', 'sklearn.tests'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CESTGui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    name='CESTGui',
)

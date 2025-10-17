# -*- mode: python ; coding: utf-8 -*-

import glob
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

def safe_collect_submodules(pkg, exclude_prefixes=[]):
    def filter_fun(name, exclude):
        for e in exclude:
            if name.find(e) >= 0:
                return False
        return True
    return collect_submodules(pkg, filter=lambda name: filter_fun(name, exclude_prefixes))

block_cipher = None

bins = []
hidden = [
    'mx.DateTime',
    'f2py',
    'pkg_resources.py2_warn',
    'pkg_resources.markers',
    'pysqlite2',
    'MySQLdb',
    'six',
    'logging.config',
    'sqlparse',
]

packages_path = '.venv\\Lib\\site-packages'
hidden.extend([Path(x).stem for x in glob.glob(glob.escape(packages_path) + "\\omero_*.py")])

hidden.extend(collect_submodules('dependency_injector'))
hidden.extend(collect_submodules('numpy'))
hidden.extend(safe_collect_submodules('omero', exclude_prefixes=['omero.testlib']))
hidden.extend(safe_collect_submodules('pyqtgraph', exclude_prefixes=['pyqtgraph.examples', 'pyqtgraph.jupiter']))

a = Analysis(
    ['iocbio\\gel\\app.py'],
    pathex=[],
    binaries=bins,
    datas=[
        ('iocbio\\gel\\db\\alembic\\', 'iocbio\\gel\\db\\alembic\\'),
        ('iocbio\\gel\\*.ini', '.'),
    ],
    hiddenimports=hidden,
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
    [],
    exclude_binaries=True,
    name='gel',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name='app',
)

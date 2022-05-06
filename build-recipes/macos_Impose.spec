# -*- mode: python ; coding: utf-8 -*-
from os.path import exists
import warnings

from impose._version import version

NAME = "Impose"


if not exists("../impose/__main__.py"):
    warnings.warn("Cannot find ../impose/__main__.py'! " +
                  "Please run pyinstaller from the 'build-recipes' directory.")

block_cipher = None

a = Analysis(['../impose/__main__.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['.'],
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name=NAME + '.bin',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name=NAME)
app = BUNDLE(coll,
             name=NAME + '.app',
             icon=NAME + '.icns',
             bundle_identifier=None,
             info_plist = {
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable' : 'True',
                'CFBundleShortVersionString' : version,
                }
             )

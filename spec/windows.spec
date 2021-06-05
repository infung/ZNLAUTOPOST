# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\Anthony\\PycharmProjects\\WeiboPost'],
             binaries=[('chromedriver.exe', '.')],
             datas=[('input.json', '.'), ('content.json', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='selenium-automation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

import shutil
shutil.copyfile('input.json', '{0}/input.json'.format(DISTPATH))
shutil.copyfile('content.json', '{0}/content.json'.format(DISTPATH))

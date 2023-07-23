# PmxDressup 64bit版

import sys

sys.path.append("src")
from executor import APP_NAME, VERSION_NAME

file_name = f"{APP_NAME}_{VERSION_NAME}"
binary_keys = []
data_keys = [
    ('src/resources/logo.ico', 'resources'),
    ('src/resources/icon/*.*', 'resources/icon'),
    ('src/i18n/en-us/LC_MESSAGES/messages.mo', 'i18n/en-us/LC_MESSAGES'),
    ('src/i18n/ja/LC_MESSAGES/messages.mo', 'i18n/ja/LC_MESSAGES'),
    ('src/i18n/ko/LC_MESSAGES/messages.mo', 'i18n/ko/LC_MESSAGES'),
    ('src/i18n/zh/LC_MESSAGES/messages.mo', 'i18n/zh/LC_MESSAGES'),
    ('mmd_base/mlib/resources/share_toon/*.*', 'mlib/resources/share_toon'),
    ('mmd_base/mlib/pmx/glsl/*.*', 'mlib/pmx/glsl'),
]
exclude_dlls = ['numpy\random\_bounded_integers.cp311-win_amd64.pyd', 'numpy\random\_common.cp311-win_amd64.pyd',
                'numpy\random\_generator.cp311-win_amd64.pyd', 'numpy\random\_mt19937.cp311-win_amd64.pyd', 'numpy\random\_pcg64.cp311-win_amd64.pyd',
                'numpy\random\_philox.cp311-win_amd64.pyd', 'numpy\random\_sfc64.cp311-win_amd64.pyd', 'numpy\random\bit_generator.cp311-win_amd64.pyd',
                'numpy\random\mtrand.cp311-win_amd64.pyd', 'libssl-3-x64.dll', 'libcrypto-3-x64.dll',
                'PIL\_webp.cp311-win_amd64.pyd', 'PIL\_imagingtk.cp311-win_amd64.pyd', 'PIL\_imagingcms.cp311-win_amd64.pyd', '_ssl.pyd', '_asyncio.pyd']

import os

def remove_from_list(input):
    outlist = []
    for item in sorted(input):
        name, path, btype = item
        flag = 0
        if name in exclude_dlls:
            flag = 1
        print(f"{' OK ' if not flag else '*NG*'} [{name}] = {flag} ({os.path.getsize(path)})")
        if flag != 1:
            outlist.append(item)
    return outlist

a = Analysis(['src/executor.py'],
            pathex=['src', 'mmd_base/mlib'],
            binaries=binary_keys,
            datas=data_keys,
            hiddenimports=[],
            hookspath=[],
            runtime_hooks=[],
            excludes=exclude_dlls,
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=None,
            noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
            cipher=None)

print('scripts -----')
a.scripts = remove_from_list(a.scripts)
# print([(f" - {s}\n") for s in a.scripts])

print('binaries -----')
a.binaries = remove_from_list(a.binaries)
# print([(f" - {s}\n") for s in a.binaries])

print('zipfiles -----')
a.zipfiles = remove_from_list(a.zipfiles)
# print([(f" - {s}\n") for s in a.zipfiles])

print('datas -----')
a.datas = remove_from_list(a.datas)
# print([(f" - {s}\n") for s in a.datas])

exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name=file_name,
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False,
            icon=data_keys[0][0])

# PmxDressup 64bit版

file_name = "PmxDressup_1.00.00_β01"
binary_keys = []
data_keys = [
    ('src/resources/pmx_dressup.ico', 'resources'),
    ('src/i18n/en-us/LC_MESSAGES/messages.mo', 'i18n/en-us/LC_MESSAGES'),
    ('src/i18n/ja/LC_MESSAGES/messages.mo', 'i18n/ja/LC_MESSAGES'),
    ('src/i18n/ko/LC_MESSAGES/messages.mo', 'i18n/ko/LC_MESSAGES'),
    ('src/i18n/zh/LC_MESSAGES/messages.mo', 'i18n/zh/LC_MESSAGES'),
]
exclude_keys = None

a = Analysis(['src/executor.py'],
            pathex=['src', 'mmd_base/mlib'],
            binaries=binary_keys,
            datas=data_keys,
            hiddenimports=[],
            hookspath=[],
            runtime_hooks=[],
            excludes=exclude_keys,
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=None,
            noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
            cipher=None)
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

import os
import subprocess

from executor import APP_NAME, VERSION_NAME

EXE_NAME = f"{APP_NAME}_{VERSION_NAME}"

for file_path, cmd, icon_loc in [
    (
        f"../dist/{EXE_NAME}.exe - en.lnk",
        f'/c start "%cd%" "{EXE_NAME}.exe" --verbose 20 --out_log 0 --lang en-us',
        '"%SystemRoot%/System32/SHELL32.dll, 0"',
    ),
    (
        f"../dist/{EXE_NAME}.exe - zh.lnk",
        f'/c start "%cd%" "{EXE_NAME}.exe" --verbose 20 --out_log 0 --lang zh',
        '"%SystemRoot%/System32/SHELL32.dll, 0"',
    ),
    (
        f"../dist/{EXE_NAME}.exe - ko.lnk",
        f'/c start "%cd%" "{EXE_NAME}.exe" --verbose 20 --out_log 0 --lang ko',
        '"%SystemRoot%/System32/SHELL32.dll, 0"',
    ),
    (
        f"../dist/{EXE_NAME}.exe - デバッグ版.lnk",
        f'/c start "%cd%" "{EXE_NAME}.exe" --verbose 10 --out_log 1 --lang ja',
        '"%SystemRoot%/System32/SHELL32.dll, 0"',
    ),
    (
        f"../dist/{EXE_NAME}.exe - ログあり版.lnk",
        f'/c start "%cd%" "{EXE_NAME}.exe" --verbose 20 --out_log 1 --lang ja',
        '"%SystemRoot%/System32/SHELL32.dll, 0"',
    ),
]:
    print("file_name: ", file_path)
    print("cmd: ", cmd)
    print("icon_loc: ", icon_loc)

    proc = subprocess.Popen(
        [
            "cscript",
            os.path.abspath("create_lnk.vbs"),
            os.path.abspath(file_path),
            "%windir%/system32/cmd.exe ",
            cmd,
            icon_loc,
        ],
    )
    proc.wait()
    proc.terminate()

from executor import APP_NAME, VERSION_NAME

EXE_NAME = f"{APP_NAME}_{VERSION_NAME}"

for file_path, args in [
    (
        f"../dist/{EXE_NAME}.exe - en.bat",
        "--verbose 20 --out_log 0 --lang en-us",
    ),
    (
        f"../dist/{EXE_NAME}.exe - zh.bat",
        "--verbose 20 --out_log 0 --lang zh",
    ),
    (
        f"../dist/{EXE_NAME}.exe - ko.bat",
        "--verbose 20 --out_log 0 --lang ko",
    ),
    (
        f"../dist/{EXE_NAME}.exe - デバッグ版.bat",
        "--verbose 10 --out_log 1 --lang ja",
    ),
    (
        f"../dist/{EXE_NAME}.exe - ログあり版.bat",
        "--verbose 20 --out_log 1 --lang ja",
    ),
]:
    print("file_name: ", file_path)
    print("args: ", args)

    with open(file_path, "w") as f:
        # start /B exe
        f.write(f"start /B {EXE_NAME}.exe {args}")

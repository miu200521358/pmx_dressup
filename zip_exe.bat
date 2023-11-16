@echo off

cd /d %~dp0

cls

call translate.bat

del dist\*.zip
del dist\*.bat
move /y dist\*.exe dist\past

call mmd_base\setup.bat

pyinstaller --clean zip_exe.spec

python create_bat.py

copy /y archive\Readme*.txt dist

call python mmd_base\setup_clear.py

rem -- 音を鳴らす
rundll32 user32.dll,MessageBeep
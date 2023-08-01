@echo off

cd /d %~dp0

cls

call translate.bat

call mmd_base\setup.bat

del dist\*.zip
del dist\*.bat
move /y dist\*.exe dist\past

pyinstaller --clean zip_exe.spec

copy /y archive\Readme*.txt dist

cd src && python create_bat.py && cd ..

call python mmd_base\setup_clear.py


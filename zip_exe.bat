@echo off

cd /d %~dp0

cls

del dist\*.zip
del dist\*.lnk
move /y dist\*.exe dist\past

pyinstaller --clean zip_exe.spec

copy /y archive\Readme*.txt dist

cd src && python create_lnk.py && cd ..


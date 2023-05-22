@echo off

cd /d %~dp0

cls

call translate.bat

del dist\*.zip
del dist\*.bat
move /y dist\*.exe dist\past

pyinstaller --clean zip_exe.spec

copy /y archive\Readme*.txt dist

cd src && python create_bat.py && cd ..


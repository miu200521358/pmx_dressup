@echo off

cd /d %~dp0

del dist/*.lnk
move /y dist/*.exe dist/past

pyinstaller --clean zip_exe.spec

copy /y archive/Readme.txt dist/Readme.txt
copy /y archive/Readme_en.txt dist/Readme_en.txt
copy /y archive/É¿î≈Readme.txt dist/É¿î≈Readme.txt

cd src && python create_lnk.py && cd ..


@echo off

set "dir=%~dp0"

python.exe -m pip install -r "%dir%\requirements.txt"
python.exe "%dir%\manage.py" migrate
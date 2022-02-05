@echo off

set "dir=%~dp0"

python.exe --version

if not exist "%dir%\db.sqlite3" (
	mkdir "packs"
	mkdir "uploads"
	mkdir "uploads\logs"
	mkdir "uploads\keys"
	copy "wizard\settings.py.tpl" "wizard\settings.py"
	copy "default.rfm" "uploads\default.rfm"
	
	if exist "%dir%\get-pip.py" (
		python.exe "%dir%\get-pip.py"
	)
	
	python.exe -m pip install -r "%dir%\requirements.txt"
	python.exe "%dir%\manage.py" migrate
	"%dir%\runaddcommon.bat"
	python.exe "%dir%\setup.py"
	python.exe "%dir%\apx.py"
)

python.exe "%dir%\apx.py"

pause
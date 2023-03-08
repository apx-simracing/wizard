set "dir=%~dp0"

REM Download the data from https://wiki.apx.chmr.eu/doku.php?id=common_components
python.exe "%dir%\createfixture.py"

REM import it
python.exe  "%dir%\manage.py" loaddata "%dir%\common.json"

REM add demo event
python.exe  "%dir%\manage.py" loaddata "%dir%\fixture.json"
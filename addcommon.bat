REM Download the data from https://wiki.apx.chmr.eu/doku.php?id=common_components
python.exe createfixture.py

REM import it
python.exe  manage.py loaddata common.json
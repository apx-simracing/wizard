@echo off
python.exe --version

if not exist "db.sqlite3" (
	mkdir packs
	mkdir uploads
	mkdir "uploads/logs"
	mkdir "uploads/keys"
	cp "wizard/settings.py.tpl" "wizard/settings.py"
	cp "default.rfm" "uploads/default.rfm"
  python.exe get-pip.py
  python.exe -m pip install -r requirements.txt
	python.exe manage.py migrate
	python.exe manage.py createsuperuser
	python.exe manage.py loaddata fixture.json
) else (
	python.exe manage.py runserver
)
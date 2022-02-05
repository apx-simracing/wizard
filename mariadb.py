from zipfile import ZipFile
from requests import get
from io import BytesIO
from os.path import join, exists
from shutil import move
from os import mkdir, getcwd,listdir
from subprocess import Popen, call
from time import sleep
import configparser

mariadb_download = "http://localhost:8181/mariadb-10.6.5-winx64.zip"
mariadb_folder = "mariadb-10.6.5-winx64"
mariadb_pass = "bockwurst"
mariadb_port = 3311



if not exists(mariadb_folder):
  print("Downloading mariaDB")
  r = get(mariadb_download)
  z = ZipFile(BytesIO(r.content))
  database_path = join(getcwd())
  z.extractall(database_path)

  #set up mysql
  #add a root user
  #https://www.techgalery.com/2019/09/how-to-install-mysql-or-mariadb.html
  #https://mariadb.com/kb/en/mysql_install_dbexe/

  print("Installing mariaDB tables")
  install_command = join(getcwd(), mariadb_folder, "bin/mysql_install_db.exe")
  args = [
    install_command,
    f"--password={mariadb_pass}"
  ]
  install_process = Popen(args)
  install_process.communicate()
  
  
  print("Startup the database")
  # create the apx database: Start mysqld
  database_command = join(getcwd(), mariadb_folder, "bin/mysqld.exe")
  args = [
    database_command
  ]
  Popen(args, shell=True)
  sleep(5)


  print("Create the database")
  # create the database: Add the database:
  database_command = join(getcwd(), mariadb_folder, "bin/mysql.exe")
  args = [
    database_command,
    "-uroot",
    f"-p{mariadb_pass}",
    "-eCREATE DATABASE apx"
  ]
  add_db_process = Popen(args, shell=True)
  add_db_process.communicate()
  

  print("Stop the database")
  stop_command = join(getcwd(), mariadb_folder, "bin/mysqladmin.exe")
  args = [
    stop_command,
    "-uroot",
    f"-p{mariadb_pass}",
    "shutdown"
  ]
  stop_process = Popen(args, shell=True)
  
  print("Adapt port")
  mariadb_config = join(getcwd(), mariadb_folder, "data", "my.ini")
  config = configparser.ConfigParser()
  config.read(mariadb_config)
  config["mysqld"]["port"] = str(mariadb_port)
  with open(mariadb_config, 'w') as configfile:
    config.write(configfile)

  
  print("Create config file") 
  my_cnf_path = join(getcwd(), "my.cnf")
  with open(my_cnf_path, "w") as file:
    file.write("[client]\n")
    file.write("database = apx\n")
    file.write("user = root\n")
    file.write(f"port = {mariadb_port}\n")
    file.write(f"password = {mariadb_pass}\n")
    file.write("default-character-set = utf8\n")
# config.py
from mysql.connector import pooling

# Configuración de la conexión MySQL
dbconfig = {
    "pool_name": "mypool",
    "pool_size": 5,
    "user": 'root',
    "password": '',
    "host": 'localhost',
    "port": '3306',
    "database": 'monitoreo_playa'
}

class Config:
    SQLALCHEMY_DATABASE_URI = f'mysql://{dbconfig["user"]}:{dbconfig["password"]}@{dbconfig["host"]}:{dbconfig["port"]}/{dbconfig["database"]}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'desarrollo-key'
    MYSQL_POOL = pooling.MySQLConnectionPool(**dbconfig)
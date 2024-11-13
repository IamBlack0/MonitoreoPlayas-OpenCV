# config.py
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la conexión MySQL
dbconfig = {
    "pool_name": "mypool",
    "pool_size": 5,
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "host": os.getenv('DB_HOST'),
    "port": os.getenv('DB_PORT'),
    "database": os.getenv('DB_NAME')
}

class Config:
    SQLALCHEMY_DATABASE_URI = f'mysql://{dbconfig["user"]}:{dbconfig["password"]}@{dbconfig["host"]}:{dbconfig["port"]}/{dbconfig["database"]}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    MYSQL_POOL = pooling.MySQLConnectionPool(**dbconfig)
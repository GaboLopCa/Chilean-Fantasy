import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def _connect(cursor_factory=None):
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT"),
        cursor_factory=cursor_factory,
    )

def get_db_connection():
    """Conexión con filas tipo diccionario (para los routers de la API)."""
    return _connect(cursor_factory=RealDictCursor)

def get_raw_db_connection():
    """Conexión con filas tipo tupla (para scripts de consola como populate_*)."""
    return _connect(cursor_factory=None)
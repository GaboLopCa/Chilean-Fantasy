from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt

SECRET_KEY = "tu_clave_secreta_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

def hash_password(password: str) -> str:
    # 1. Truncar manualmente a 72 bytes en UTF-8 para cumplir el límite estricto de bcrypt
    pwd_bytes = password.encode('utf-8')[:72]
    # 2. Generar el salt y el hash usando directamente la librería bcrypt
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
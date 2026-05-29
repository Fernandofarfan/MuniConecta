import logging
from datetime import UTC

import bcrypt
from fastapi import Header, HTTPException
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import API_KEY, JWT_ALGORITHM, JWT_SECRET

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def crear_hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verificar_password(password: str, hashed: str) -> bool:
    pwd_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def crear_jwt(data: dict) -> str:
    from datetime import datetime, timedelta

    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(hours=12)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


async def verificar_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    if not API_KEY:
        logger.warning("API_KEY no configurada; aceptando cualquier request")
        return "no-key-configured"
    if x_api_key != API_KEY:
        logger.warning("Intento de acceso con API key invalida")
        raise HTTPException(status_code=401, detail="API Key invalida")
    return x_api_key


async def verificar_jwt(authorization: str = Header(None), x_api_key: str = Header(None, alias="X-API-Key")) -> dict:
    if API_KEY and x_api_key == API_KEY:
        # Bypass for internal services (e.g. Dashboard)
        return {"sub": "system", "rol": "admin"}

    if not JWT_SECRET:
        return {"sub": "anonymous", "rol": "public"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token JWT requerido. Usa Authorization: Bearer <token>")

    token = authorization.split(" ", 1)[1]
    payload = decodificar_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token JWT invalido o expirado")

    return payload

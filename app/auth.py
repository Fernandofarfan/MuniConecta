import logging

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import API_KEY

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


async def verificar_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    if not API_KEY:
        logger.warning("API_KEY no configurada; aceptando cualquier request")
        return "no-key-configured"

    if x_api_key != API_KEY:
        logger.warning("Intento de acceso con API key invalida")
        raise HTTPException(status_code=401, detail="API Key invalida")

    return x_api_key

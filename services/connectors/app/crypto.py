import json

import structlog
from cryptography.fernet import Fernet

from app.core.config import settings

logger = structlog.get_logger()


def encrypt_credentials(credentials: dict) -> dict:
    if settings.ENCRYPTION_KEY is None:
        logger.warning("crypto.encrypt.no_key")
        return credentials
    f = Fernet(settings.ENCRYPTION_KEY.encode())
    token = f.encrypt(json.dumps(credentials).encode())
    return {"encrypted": token.decode()}


def decrypt_credentials(stored: dict) -> dict:
    if "encrypted" not in stored:
        return stored
    if settings.ENCRYPTION_KEY is None:
        logger.warning("crypto.decrypt.no_key")
        return stored
    try:
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        data = f.decrypt(stored["encrypted"].encode())
        return json.loads(data)
    except Exception as exc:
        logger.error("crypto.decrypt.failed", error=str(exc))
        return {}

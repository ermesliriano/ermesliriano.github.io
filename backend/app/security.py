import datetime as dt
import hashlib
import secrets
from typing import Any

import jwt
from passlib.hash import argon2

from .config import settings

def hash_password(password: str) -> str:
    # Argon2id recomendado por OWASP; passlib permite ajustar parámetros si quieres.
    return argon2.using(type="ID").hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)

def create_access_token(*, subject: str, extra: dict[str, Any] | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    exp = now + dt.timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

def new_refresh_token() -> str:
    # opaco; no JWT. Rotación y revocación más sencilla.
    return secrets.token_urlsafe(48)

def refresh_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

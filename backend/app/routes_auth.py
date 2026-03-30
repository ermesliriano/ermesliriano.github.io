import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from .config import settings
from .db import get_db
from .models import User, RefreshToken
from .schemas import RegisterRequest, LoginRequest, GoogleLoginRequest, TokenPair
from .security import (
    hash_password, verify_password,
    create_access_token,
    new_refresh_token, refresh_token_hash,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

def _issue_tokens(db: Session, user: User, request: Request) -> TokenPair:
    access = create_access_token(subject=user.id, extra={"email": user.email})
    refresh = new_refresh_token()
    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash(refresh),
        expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=settings.REFRESH_TOKEN_DAYS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(rt)
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)

@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email ya registrado")

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return {"ok": True}

@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    # Evitar enumeración: misma respuesta genérica
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    db.add(user)
    db.commit()
    return _issue_tokens(db, user, request)

@router.post("/google", response_model=TokenPair)
def google_login(payload: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.GOOGLE_WEB_CLIENT_ID,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="ID token de Google inválido")

    # Claims esperadas OIDC: sub, email (si scope email), email_verified, etc.
    sub = idinfo.get("sub")
    email = (idinfo.get("email") or "").lower()
    if not sub:
        raise HTTPException(status_code=401, detail="Falta claim sub")

    # Recomendación: no usar email como ID único; usar sub.
    user = db.query(User).filter(User.google_sub == sub).first()

    if not user and email:
        # Si ya existe el email por login local, se puede "linkear"
        user = db.query(User).filter(User.email == email).first()
        if user and not user.google_sub:
            user.google_sub = sub

    if not user:
        if not email:
            # Si no pediste scope email, puede no venir email. En MVP exigimos email.
            raise HTTPException(status_code=400, detail="Google no devolvió email; revisa scopes")
        user = User(email=email, google_sub=sub, password_hash=None)

    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    db.add(user)
    db.commit()
    return _issue_tokens(db, user, request)

@router.post("/refresh", response_model=TokenPair)
def refresh(refresh_token: str, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    now = dt.datetime.now(dt.timezone.utc)
    h = refresh_token_hash(refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == h).first()
    if not rt or rt.revoked_at is not None or rt.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user = db.query(User).filter(User.id == rt.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inválido")

    # Rotación: revoca el antiguo y emite uno nuevo
    rt.revoked_at = now
    db.add(rt)
    db.commit()

    return _issue_tokens(db, user, request)

@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)) -> dict:
    h = refresh_token_hash(refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == h).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = dt.datetime.now(dt.timezone.utc)
        db.add(rt)
        db.commit()
    return {"ok": True}

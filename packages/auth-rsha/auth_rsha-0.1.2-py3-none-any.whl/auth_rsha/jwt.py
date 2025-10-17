# src/auth_rsha/jwt.py
from jose import jwt, JWTError, ExpiredSignatureError 
from datetime import datetime, timedelta, timezone
from .schemas import TokenPayload
from .config import AuthSettings

def create_access_token(payload: TokenPayload, settings: AuthSettings) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.access_ttl)
    data = {
        "sub": payload.sub,
        "role": payload.role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if settings.issuer: data["iss"] = settings.issuer
    if settings.audience: data["aud"] = settings.audience
    token = jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_alg, headers={"typ":"JWT"})
    return token, settings.access_ttl

def decode_token(token: str, settings: AuthSettings) -> TokenPayload:
    try:
        data = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            # leeway надо передавать через options
            options={
                "verify_aud": bool(settings.audience),
                "leeway": settings.leeway_sec,
            },
            audience=settings.audience,
            issuer=settings.issuer,
        )
        return TokenPayload(sub=str(data["sub"]), role=data.get("role"))
    except ExpiredSignatureError as e:
        raise e
    except JWTError as e:
        raise e

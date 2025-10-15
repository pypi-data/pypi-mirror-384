from jose import jwt
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
    token = jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_alg)
    return token, settings.access_ttl

def decode_token(token: str, settings: AuthSettings) -> TokenPayload:
    data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    return TokenPayload(sub=data["sub"], role=data.get("role"))

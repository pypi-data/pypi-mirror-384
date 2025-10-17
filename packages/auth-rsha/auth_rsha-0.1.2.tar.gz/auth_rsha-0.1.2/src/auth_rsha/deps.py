# src/auth_rsha/deps.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from .config import AuthSettings
from .jwt import decode_token
from .schemas import TokenPayload

def make_current_user(settings: AuthSettings):
    oauth2 = OAuth2PasswordBearer(
        tokenUrl=settings.token_url_path,
        scheme_name="Bearer",
        auto_error=True,
    )
    async def current_user(token: Annotated[str, Depends(oauth2)]) -> TokenPayload:
        try:
            return decode_token(token, settings)
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return current_user

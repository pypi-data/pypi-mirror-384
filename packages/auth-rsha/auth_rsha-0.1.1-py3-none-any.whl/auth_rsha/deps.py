from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .config import AuthSettings
from .jwt import decode_token
from .schemas import TokenPayload

def make_current_user(settings: AuthSettings):
    oauth2 = OAuth2PasswordBearer(tokenUrl=settings.token_url_path)
    async def current_user(token: str = Depends(oauth2)) -> TokenPayload:
        try:
            return decode_token(token, settings)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return current_user

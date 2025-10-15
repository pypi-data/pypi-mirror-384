from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..schemas import Token, UserInDB, TokenPayload
from ..hashing import verify_password
from ..config import AuthSettings
from ..repo import UserRepository
from ..jwt import create_access_token

def make_auth_router(settings: AuthSettings, repo: UserRepository) -> APIRouter:
    router = APIRouter(tags=["auth"])

    @router.post(settings.token_url_path, response_model=Token)
    async def issue_token(form: OAuth2PasswordRequestForm = Depends()):
        user: UserInDB | None = await repo.get_by_username(form.username)
        if not user or not user.is_active or not verify_password(form.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token, ttl = create_access_token(TokenPayload(sub=user.id, role=user.role), settings)
        return Token(access_token=token, expires_in=ttl)

    return router

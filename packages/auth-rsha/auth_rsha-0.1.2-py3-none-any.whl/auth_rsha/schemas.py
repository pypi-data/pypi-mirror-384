from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    sub: str
    role: Optional[str] = None

class UserInDB(BaseModel):
    id: str
    username: str
    password_hash: str
    role: Optional[str] = None
    is_active: bool = True

from pydantic import BaseModel, Field

class AuthSettings(BaseModel):
    jwt_secret: str = Field(..., min_length=32)
    jwt_alg: str = "HS256"
    access_ttl: int = 3600
    token_url_path: str = "/auth/token"

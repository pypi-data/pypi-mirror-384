# src/auth_rsha/hashing.py
from passlib.context import CryptContext

_pwd = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # можно выставить параметры argon2 если нужно
)

def hash_password(plain: str) -> str:
    return _pwd.hash(plain[:512])  

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)

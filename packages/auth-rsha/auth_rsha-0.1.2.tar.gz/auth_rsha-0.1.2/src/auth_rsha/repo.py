from typing import Protocol, Optional
from .schemas import UserInDB

class UserRepository(Protocol):
    async def get_by_username(self, username: str) -> Optional[UserInDB]:
        ...

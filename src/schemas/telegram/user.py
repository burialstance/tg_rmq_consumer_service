from typing import Optional
from pydantic import BaseModel


class TelegramUserSchema(BaseModel):
    id: int
    is_bot: bool
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True

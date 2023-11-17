import enum
from typing import Optional

from pydantic import BaseModel


class TelegramChatSchema(BaseModel):
    class ChatType(enum.Enum):
        PRIVATE = 'PRIVATE'
        BOT = 'BOT'
        GROUP = 'GROUP'
        SUPERGROUP = 'SUPERGROUP'
        CHANNEL = 'CHANNEL'

    id: int
    type: ChatType
    title: Optional[str] = None
    username: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None

    class Config:
        from_attributes = True

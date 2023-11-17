import datetime
from typing import Optional, Any
import time
from pydantic import BaseModel

from src.schemas.telegram.user import TelegramUserSchema
from src.schemas.telegram.chat import TelegramChatSchema


class TelegramMessageSchema(BaseModel):
    id: int
    date: Optional[datetime.datetime] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    empty: Optional[bool] = None

    from_user: Optional[TelegramUserSchema] = None
    chat: Optional[TelegramChatSchema] = None
    reply_to_message: Optional['TelegramMessageSchema'] = None

    class Config:
        from_attributes = True

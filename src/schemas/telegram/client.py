from typing import Optional

from pydantic import BaseModel

from src.schemas.telegram.user import TelegramUserSchema


class TelegramClientSchema(BaseModel):
    name: str
    app_version: Optional[str]
    device_model: Optional[str]
    system_version: Optional[str]
    is_connected: Optional[bool]
    is_initialized: Optional[bool]

    me: Optional[TelegramUserSchema]

    class Config:
        from_attributes = True

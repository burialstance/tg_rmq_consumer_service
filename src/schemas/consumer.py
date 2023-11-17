from typing import List

from pydantic import BaseModel

from src.schemas.telegram.message import TelegramMessageSchema


class ConsumerResponse(BaseModel):
    telegram_message: TelegramMessageSchema
    cryptoboxes: List[str]

from pydantic import BaseModel

from src.schemas.telegram.message import TelegramMessageSchema
from src.schemas.telegram.client import TelegramClientSchema


class ProducerMessage(BaseModel):
    client: TelegramClientSchema

    class Config:
        from_attributes = True


class ProducerRawMessage(ProducerMessage):
    raw_message: TelegramMessageSchema

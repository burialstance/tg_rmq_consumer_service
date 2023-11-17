import enum
from typing import Optional

from tortoise import Model, fields


class TelegramChat(Model):
    class ChatType(str, enum.Enum):
        PRIVATE = 'PRIVATE'
        BOT = 'BOT'
        GROUP = 'GROUP'
        SUPERGROUP = 'SUPERGROUP'
        CHANNEL = 'CHANNEL'

    id: int = fields.BigIntField(pk=True, index=True)
    type: ChatType = fields.CharEnumField(ChatType)
    title: Optional[str] = fields.CharField(64, null=True)
    username: Optional[str] = fields.CharField(255, null=True, unique=True)
    description: Optional[str] = fields.CharField(4096, null=True)
    members_count: Optional[int] = fields.IntField(null=True)

    blacklist: fields.ReverseRelation

    messages: fields.ReverseRelation

    class Meta:
        table = 'telegram_chat'

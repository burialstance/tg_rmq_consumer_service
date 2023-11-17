import datetime
from typing import Optional, Self

from tortoise import Model, fields
from tortoise.expressions import Q
from tortoise.manager import Manager
from tortoise.queryset import QuerySet


class TelegramMessageQueryset(QuerySet):
    def search(self, q: str) -> Self:
        return self.filter(Q(
            text__contains=q,
            caption__contains=q,
            join_type='OR'
        ))

    def by_user_id(self, from_user_id: int) -> Self:
        return self.filter(from_user_id=from_user_id)

    def by_chat_id(self, chat_id: int) -> Self:
        return self.filter(chat_id=chat_id)


class TelegramMessageManager(Manager):
    def get_queryset(self) -> TelegramMessageQueryset:
        return TelegramMessageQueryset(TelegramMessage)


class TelegramMessage(Model):
    message_id: int = fields.BigIntField()
    date: datetime.datetime = fields.DatetimeField()
    text: Optional[str] = fields.CharField(4096, null=True)
    caption: Optional[str] = fields.CharField(4096, null=True)
    empty: Optional[bool] = fields.BooleanField(null=True)

    chat: fields.ForeignKeyRelation = fields.ForeignKeyField('telegram.TelegramChat', 'messages')
    from_user: fields.ForeignKeyRelation = fields.ForeignKeyField('telegram.TelegramUser', 'messages', null=True)

    reply_to_message: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        'telegram.TelegramMessage', 'replies', null=True
    )
    replies: fields.ReverseRelation

    objects = TelegramMessageManager()

    class Meta:
        unique_together = ('chat_id', 'message_id')
        ordering = ['-date']
        table = 'telegram_message'

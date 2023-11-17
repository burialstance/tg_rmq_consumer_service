from tortoise import fields

from src.db import mixins

from .base import BlacklistBaseModel, BlacklistManager, BlacklistQueryset


class TelegramChatBlacklistManager(BlacklistManager):
    def get_queryset(self) -> BlacklistQueryset:
        return BlacklistQueryset(TelegramChatBlacklist)


class TelegramChatBlacklist(mixins.Timestamped, BlacklistBaseModel):
    chat: fields.ForeignKeyRelation['TelegramChat'] = fields.ForeignKeyField(
        'telegram.TelegramChat', 'blacklist'
    )

    objects = TelegramChatBlacklistManager()

    class Meta:
        table = 'telegram_chat_blacklist'

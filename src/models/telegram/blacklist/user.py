from tortoise import fields

from src.db import mixins
from .base import BlacklistBaseModel, BlacklistManager, BlacklistQueryset


class TelegramUserBlacklistManager(BlacklistManager):
    def get_queryset(self) -> BlacklistQueryset:
        return BlacklistQueryset(TelegramUserBlacklist)


class TelegramUserBlacklist(mixins.Timestamped, BlacklistBaseModel):
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        'telegram.TelegramUser', 'blacklist',
    )

    objects = TelegramUserBlacklistManager()

    class Meta:
        table = 'telegram_user_blacklist'

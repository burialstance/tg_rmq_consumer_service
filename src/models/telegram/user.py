from typing import Optional

from tortoise import Model, fields


class TelegramUser(Model):
    id: int = fields.BigIntField(pk=True, index=True)
    is_bot: bool = fields.BooleanField()
    username: Optional[str] = fields.CharField(64, unique=True, null=True)
    first_name: Optional[str] = fields.CharField(64, null=True)
    last_name: Optional[str] = fields.CharField(64, null=True)
    bio: Optional[str] = fields.CharField(max_length=512, null=True)

    blacklist: fields.ReverseRelation

    messages: fields.ReverseRelation

    class Meta:
        table = 'telegram_user'

    @property
    def full_name(self) -> Optional[str]:
        return ' '.join(filter(None, [self.first_name, self.last_name]))


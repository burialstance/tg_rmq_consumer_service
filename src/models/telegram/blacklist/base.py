import datetime
from typing import Self, Optional

import humanize
from tortoise import Model, fields
from tortoise.expressions import Q
from tortoise.manager import Manager
from tortoise.queryset import QuerySet
from tortoise.timezone import now


class BlacklistQueryset(QuerySet):
    def not_amnestied(self) -> Self:
        return self.filter(amnestied_at__isnull=True)

    def not_released(self) -> Self:
        return self.filter(Q(
            release_at__isnull=True,
            release_at__gt=now(),
            join_type='OR'
        ))

    def restricted(self) -> Self:
        return self.not_released().not_amnestied()


class BlacklistManager(Manager):
    def get_queryset(self) -> BlacklistQueryset:
        return BlacklistQueryset(BlacklistBaseModel)


class BlacklistBaseModel(Model):
    reason: Optional[str] = fields.CharField(512, null=True)
    release_at: Optional[datetime.datetime] = fields.DatetimeField(null=True)
    amnestied_at: Optional[datetime.datetime] = fields.DatetimeField(null=True)
    amnestied_reason: Optional[str] = fields.CharField(512, null=True)

    class Meta:
        abstract = True

    @property
    def release_remaining(self) -> Optional[datetime.timedelta]:
        if self.release_at:
            return now() - self.release_at

    @property
    def release_at_humanize(self) -> str:
        if self.release_at is None:
            return 'permanent'
        return humanize.naturaltime(self.release_remaining)

    @property
    def amnestied_at_humanize(self) -> Optional[str]:
        if self.amnestied_at:
            return humanize.naturaldelta(now() - self.amnestied_at)
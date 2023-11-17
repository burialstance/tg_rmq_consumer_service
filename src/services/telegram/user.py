import datetime
import asyncio
from typing import Any, Optional, Union, Tuple, List, Dict

from aiocache import caches, cached, SimpleMemoryCache
from tortoise import BaseDBAsyncClient
from tortoise.exceptions import DoesNotExist, IntegrityError, TransactionManagementError
from tortoise.functions import Count
from tortoise.query_utils import Prefetch
from tortoise.queryset import QuerySet
from tortoise.signals import post_save, post_delete
from tortoise.timezone import now
from tortoise.transactions import in_transaction

from src.models.telegram import TelegramUser, TelegramUserBlacklist


class TelegramUserAlreadyBlacklisted(Exception):
    ...


class TelegramUserIsNotRestricted(Exception):
    ...


cache_alias = 'telegram_user'
caches.add(cache_alias, {
    'ttl': 300,
    'cache': "aiocache.SimpleMemoryCache",
    'serializer': {
        'class': "aiocache.serializers.NullSerializer"
    }
})

cache: SimpleMemoryCache = caches.get(cache_alias)


def get_cache_detail():
    assert isinstance(cache, SimpleMemoryCache), 'this available only on SimpleMemoryCache'
    items = []
    loop_time = asyncio.get_running_loop().time()
    for cache_key in cache._cache.keys():
        item = {'key': cache_key}
        if handler := cache._handlers.get(cache_key):
            item.update({'ttl': round(handler.when() - loop_time, 2)})
        items.append(item)

    return {
        'ttl': cache.ttl,
        'total': len(items),
        'items': items
    }


async def invalidate_cache(key: Any):
    await cache.delete(key)


@post_save(TelegramUser, TelegramUserBlacklist)
async def on_models_save(
        sender, instance: Union[TelegramUser, TelegramUserBlacklist], created, using_db, update_fields
):
    if not created:
        if isinstance(instance, TelegramUser):
            await invalidate_cache(instance.id)
        elif isinstance(instance, TelegramUserBlacklist):
            await invalidate_cache(instance.user_id)


@post_delete(TelegramUser, TelegramUserBlacklist)
async def on_models_delete(sender, instance: Union[TelegramUser, TelegramUserBlacklist], using_db):
    if isinstance(instance, TelegramUser):
        await invalidate_cache(instance.id)
    elif isinstance(instance, TelegramUserBlacklist):
        await invalidate_cache(instance.user_id)


class TelegramUserService:
    def get_queryset(self) -> QuerySet[TelegramUser]:
        return TelegramUser.all().annotate(
            messages_count=Count('messages')
        ).prefetch_related(Prefetch('blacklist', TelegramUserBlacklist.objects.restricted()))

    @cached(alias=cache_alias, key_builder=lambda f, *args, **kwargs: kwargs.get('id', args[-1]))
    async def get_by_id(self, id: int, using_db: Optional[BaseDBAsyncClient] = None) -> TelegramUser:
        return await self.get_queryset().using_db(using_db).get(id=id)

    async def create(self, using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any) -> TelegramUser:
        return await TelegramUser.create(using_db=using_db, **kwargs)

    async def update(
            self, user: TelegramUser, data: Dict, using_db: Optional[BaseDBAsyncClient] = None
    ) -> None:
        await user.update_from_dict(data).save(using_db=using_db)

    async def get_or_create(
            self, id: int, defaults: Optional[dict] = None, using_db: Optional[BaseDBAsyncClient] = None
    ) -> Tuple[TelegramUser, bool]:
        if not defaults:
            defaults = {}
        db = using_db or TelegramUser._choose_db(True)
        async with in_transaction(connection_name=db.connection_name) as connection:
            try:
                return await self.get_by_id(id=id), False
            except DoesNotExist:
                try:
                    defaults.update({'id': id})
                    return await self.create(using_db=connection, **defaults), True
                except (IntegrityError, TransactionManagementError):
                    return await self.get_by_id(id=id), False

    async def add_to_blacklist(
            self, user_id: int, reason: Optional[str] = None, release_at: Optional[datetime.datetime] = None
    ) -> TelegramUserBlacklist:
        if await TelegramUserBlacklist.objects.get_queryset().restricted().filter(user_id=user_id).exists():
            raise TelegramUserAlreadyBlacklisted
        return await TelegramUserBlacklist.create(user_id=user_id, reason=reason, release_at=release_at)

    async def is_restricted(self, user_id: int) -> bool:
        try:
            user = await self.get_by_id(id=user_id)
            return len(user.blacklist) != 0
        except DoesNotExist:
            pass
        return False

    async def remove_from_blacklist(
            self, user_id: int, amnestied_reason: Optional[str] = None
    ) -> List[TelegramUserBlacklist]:
        active_violations = await TelegramUserBlacklist.objects.get_queryset().restricted().filter(user_id=user_id)
        if not active_violations:
            raise TelegramUserIsNotRestricted

        amnestied_violations: List[TelegramUserBlacklist] = []
        for violation in active_violations:
            await violation.update_from_dict(dict(
                amnestied_reason=amnestied_reason,
                amnestied_at=now()
            )).save()
            amnestied_violations.append(violation)
        return active_violations


telegram_user_service = TelegramUserService()

if __name__ == '__main__':
    import asyncio
    from pprint import pprint
    from src.db import init_orm, close_orm
    from src.schemas.telegram.user import TelegramUserRetrieveDetail

    user_id = 7560360


    async def main():
        await init_orm()

        user: TelegramUser = await telegram_user_service.get_by_id(user_id)
        pprint(TelegramUserRetrieveDetail.model_validate(user).model_dump())

        if user.blacklist:
            await telegram_user_service.remove_from_blacklist(user.id, 'test')
            print('remove from blacklist')
        else:
            await telegram_user_service.add_to_blacklist(user.id, 'test')
            print('add to blacklist')

        user: TelegramUser = await telegram_user_service.get_by_id(user_id)
        pprint(TelegramUserRetrieveDetail.model_validate(user).model_dump())

        return user


    chat = asyncio.run(main())

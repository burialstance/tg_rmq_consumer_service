import asyncio
import datetime
from typing import Any, List, Optional, Type, Union, Tuple, Dict

from aiocache import caches, cached, SimpleMemoryCache
from tortoise import BaseDBAsyncClient
from tortoise.exceptions import DoesNotExist, TransactionManagementError, IntegrityError
from tortoise.functions import Count
from tortoise.models import MODEL
from tortoise.query_utils import Prefetch
from tortoise.queryset import QuerySet
from tortoise.signals import post_save, post_delete, Signals
from tortoise.timezone import now
from tortoise.transactions import in_transaction

from src.models.telegram import TelegramChat, TelegramChatBlacklist


class TelegramChatAlreadyBlacklisted(Exception):
    ...


class TelegramChatIsNotRestricted(Exception):
    ...


cache_alias = 'telegram_chat'
caches.add(cache_alias, {
    'ttl': 300,
    'cache': "aiocache.SimpleMemoryCache",
    'serializer': {
        'class': "aiocache.serializers.NullSerializer"
    }
})

cache: SimpleMemoryCache = caches.get(cache_alias)


async def invalidate_cache(key: Any):
    await cache.delete(key)


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


@post_save(TelegramChat, TelegramChatBlacklist)
async def on_models_save(sender, instance: Union[TelegramChat, TelegramChatBlacklist], created, using_db,
                         update_fields):
    if not created:
        if isinstance(instance, TelegramChat):
            await invalidate_cache(instance.id)
        elif isinstance(instance, TelegramChatBlacklist):
            await invalidate_cache(instance.chat_id)


@post_delete(TelegramChat, TelegramChatBlacklist)
async def on_models_delete(sender, instance: Union[TelegramChat, TelegramChatBlacklist], using_db):
    if isinstance(instance, TelegramChat):
        await invalidate_cache(instance.id)
    elif isinstance(instance, TelegramChatBlacklist):
        await invalidate_cache(instance.chat_id)


class TelegramChatService:
    def get_queryset(self) -> QuerySet[TelegramChat]:
        return TelegramChat.all().annotate(
            messages_count=Count('messages')
        ).prefetch_related(Prefetch('blacklist', TelegramChatBlacklist.objects.restricted()))

    @cached(alias=cache_alias, key_builder=lambda f, *args, **kwargs: kwargs.get('id', args[-1]))
    async def get_by_id(self, id: int, using_db: Optional[BaseDBAsyncClient] = None) -> TelegramChat:
        return await self.get_queryset().using_db(using_db).get(id=id)

    async def create(self, using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any) -> TelegramChat:
        return await TelegramChat.create(using_db=using_db, **kwargs)

    async def update(
            self, chat: TelegramChat, data: Dict, using_db: Optional[BaseDBAsyncClient] = None
    ) -> None:
        await chat.update_from_dict(data).save(using_db=using_db)

    async def get_or_create(
            self, id: int, defaults: Optional[dict] = None, using_db: Optional[BaseDBAsyncClient] = None
    ) -> Tuple[TelegramChat, bool]:
        if not defaults:
            defaults = {}
        db = using_db or TelegramChat._choose_db(True)
        async with in_transaction(connection_name=db.connection_name) as connection:
            try:
                return await self.get_by_id(id=id, using_db=connection), False
            except DoesNotExist:
                try:
                    defaults.update(dict(id=id))
                    return await self.create(using_db=connection, **defaults), True
                except (IntegrityError, TransactionManagementError):
                    return await self.get_by_id(id=id, using_db=connection), False

    async def add_to_blacklist(
            self, chat_id: int, reason: Optional[str] = None, release_at: Optional[datetime.datetime] = None
    ) -> TelegramChatBlacklist:
        if await TelegramChatBlacklist.objects.get_queryset().restricted().filter(chat_id=chat_id).exists():
            raise TelegramChatAlreadyBlacklisted
        return await TelegramChatBlacklist.create(chat_id=chat_id, reason=reason, release_at=release_at)

    async def is_restricted(self, chat_id: int) -> bool:
        try:
            chat = await self.get_by_id(id=chat_id)
            return len(chat.blacklist) != 0
        except DoesNotExist:
            pass
        return False

    async def remove_from_blacklist(
            self, chat_id: int, amnestied_reason: Optional[str] = None
    ) -> List[TelegramChatBlacklist]:
        active_violations = await TelegramChatBlacklist.objects.get_queryset().restricted().filter(chat_id=chat_id)
        if not active_violations:
            raise TelegramChatIsNotRestricted

        amnestied_violations: List[TelegramChatBlacklist] = []
        for violation in amnestied_violations:
            await violation.update_from_dict(dict(
                amnestied_reason=amnestied_reason,
                amnestied_at=now()
            )).save()
            amnestied_violations.append(violation)
        return amnestied_violations


telegram_chat_service = TelegramChatService()

# if __name__ == '__main__':
#     import asyncio
#     from pprint import pprint
#     from src.db import init_orm, close_orm
#     from src.schemas.telegram.chat import TelegramChatRetrieveDetail
#
#     chat_id = -1001981430602
#
#
#     async def main():
#         await init_orm()
#
#         service = TelegramChatService()
#         chat: TelegramChat = await service.get_by_id(chat_id)
#         pprint(TelegramChatRetrieveDetail.model_validate(chat).model_dump())
#
#         if chat.blacklist:
#             await service.remove_from_blacklist(chat.id, 'test')
#             print('remove from blacklist')
#         else:
#             await service.add_to_blacklist(chat.id, 'test')
#             print('add to blacklist')
#
#         chat: TelegramChat = await service.get_by_id(chat_id)
#         pprint(TelegramChatRetrieveDetail.model_validate(chat).model_dump())
#
#         return chat
#
#
#     chat = asyncio.run(main())

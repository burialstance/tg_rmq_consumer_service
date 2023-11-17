import asyncio
from typing import Any, Optional, Tuple

from aiocache import caches, cached, SimpleMemoryCache
from tortoise import BaseDBAsyncClient
from tortoise.exceptions import DoesNotExist, IntegrityError, TransactionManagementError
from tortoise.queryset import QuerySet
from tortoise.signals import post_save, post_delete
from tortoise.transactions import in_transaction

from src.models.telegram import TelegramMessage
from src.schemas.telegram.message import TelegramMessageSchema
from src.services.telegram.chat import telegram_chat_service
from src.services.telegram.user import telegram_user_service

cache_alias = 'telegram_message'
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


def key_builder(chat_id: int, message_id: int) -> str:
    return f'{chat_id}_{message_id}'


def cache_key_builder(f, *args, **kwargs) -> str:
    return key_builder(
        chat_id=kwargs.get('chat_id'),
        message_id=kwargs.get('message_id')
    )


def get_cache_detail() -> dict:
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


@post_save(TelegramMessage)
async def on_telegram_massage_save(sender, instance: TelegramMessage, created, using_db, update_fields):
    if created:
        return
    await invalidate_cache(key=key_builder(chat_id=instance.chat_id, message_id=instance.message_id))


@post_delete(TelegramMessage)
async def on_telegram_massage_delete(sender, instance: TelegramMessage, using_db):
    await invalidate_cache(key=key_builder(chat_id=instance.chat_id, message_id=instance.message_id))


class TelegramMessageService:
    def get_queryset(self) -> QuerySet[TelegramMessage]:
        return TelegramMessage.all()

    @cached(alias=cache_alias, key_builder=cache_key_builder)
    async def get_by_chat_id_message_id(
            self, chat_id: int, message_id: int, using_db: Optional[BaseDBAsyncClient] = None
    ):
        return await self.get_queryset().using_db(using_db).filter(chat_id=chat_id, message_id=message_id).get()

    async def create(self, using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any) -> TelegramMessage:
        return await TelegramMessage.create(using_db=using_db, **kwargs)

    async def get_or_create(
            self,
            chat_id: int,
            message_id: int,
            defaults: Optional[dict] = None,
            using_db: Optional[BaseDBAsyncClient] = None
    ) -> Tuple[TelegramMessage, bool]:
        if not defaults:
            defaults = {}
        db = using_db or TelegramMessage._choose_db(True)
        async with in_transaction(connection_name=db.connection_name) as connection:
            try:
                return await self.get_by_chat_id_message_id(chat_id=chat_id, message_id=message_id), False
            except DoesNotExist:
                try:
                    defaults.update({'chat_id': chat_id, 'message_id': message_id})
                    return await self.create(using_db=connection, **defaults), True
                except (IntegrityError, TransactionManagementError):
                    return await self.get_by_chat_id_message_id(chat_id=chat_id, message_id=message_id), False

    async def get_or_create_from_schema(
            self,
            message: TelegramMessageSchema,
            using_db: Optional[BaseDBAsyncClient] = None
    ) -> Tuple[TelegramMessage, bool]:
        message_kwargs = dict(
            message_id=message.id,
            date=message.date,
            text=message.text,
            caption=message.caption,
            empty=message.empty,
        )
        db = using_db or TelegramMessage._choose_db(True)
        async with in_transaction(connection_name=db.connection_name) as connection:
            if message.chat:
                message_kwargs['chat'], _ = await telegram_chat_service.get_or_create(
                    id=message.chat.id,
                    defaults=message.chat.model_dump(),
                    using_db=connection
                )
            if message.from_user:
                message_kwargs['from_user'], _ = await telegram_user_service.get_or_create(
                    id=message.from_user.id,
                    defaults=message.from_user.model_dump(),
                    using_db=connection
                )
            if message.reply_to_message:
                reply_to_message, _ = await self.get_or_create_from_schema(
                    message.reply_to_message, using_db=connection
                )
                message_kwargs['reply_to_message'] = reply_to_message

            return await self.get_or_create(
                chat_id=message.chat.id,
                message_id=message.id,
                defaults=message_kwargs,
                using_db=connection,
            )


telegram_message_service = TelegramMessageService()

import textwrap
from typing import Optional, List

from faststream import Logger, Depends
from faststream.rabbit import RabbitRouter

from src.adapters.rabbitmq.queues import telegram_exchange, message_queue

from src.services.parsers.text import cryptobox_parser
from src.schemas.telegram.message import TelegramMessageSchema
from src.schemas.telegram.client import TelegramClientSchema
from src.services.telegram.chat import telegram_chat_service
from src.services.telegram.messages import telegram_message_service
from src.services.telegram.user import telegram_user_service

from src import metrics


async def get_cryptoboxes(message: TelegramMessageSchema) -> Optional[List[str]]:
    return await cryptobox_parser(message.text or message.caption)


async def is_source_restricted(message: TelegramMessageSchema) -> bool:
    if message.from_user and await telegram_user_service.is_restricted(message.from_user.id):
        metrics.TELEGRAM_RESTRICTED_USER_MESSAGES.labels(
            user_id=message.from_user.id,
            user_username=message.from_user.username
        ).inc()
        return True
    elif message.chat and await telegram_chat_service.is_restricted(message.chat.id):
        metrics.TELEGRAM_RESTRICTED_CHAT_MESSAGES.labels(
            chat_id=message.chat.id,
            chat_title=message.chat.title
        ).inc()
        return True

    return False

router = RabbitRouter()


@router.subscriber(queue=message_queue, exchange=telegram_exchange)
async def on_message(
        message: TelegramMessageSchema,
        client: TelegramClientSchema,
        logger: Logger,
        cryptoboxes: Optional[List[str]] = Depends(get_cryptoboxes)
):
    if not cryptoboxes:
        return
    if await is_source_restricted(message):
        return

    message_instance, _ = await telegram_message_service.get_or_create_from_schema(message)

    # push message to rmq

    logger.info(' '.join([
        str(cryptoboxes),
        textwrap.shorten(message.text or message.caption, 32)
    ]))


from faststream import Logger
from faststream.rabbit import RabbitRouter

from src.adapters.rabbitmq.queues import reply_to_message_queue, telegram_exchange
from src.schemas.telegram.client import TelegramClientSchema
from src.schemas.telegram.message import TelegramMessageSchema
from src.services.parsers.text import cryptobox_parser
from src.services.reply_guard.guard import guard

router = RabbitRouter()


@router.subscriber(queue=reply_to_message_queue, exchange=telegram_exchange)
async def on_reply_to_message(
        message: TelegramMessageSchema,
        client: TelegramClientSchema,
        logger: Logger,
):
    cryptoboxes = await cryptobox_parser(message.reply_to_message.text or message.reply_to_message.caption)
    if not cryptoboxes:
        return

    if await guard(message.text or message.caption) is None:
        ...

    logger.info('>>'.join([
        message.text or message.caption,
        message.reply_to_message.text or message.reply_to_message.caption
    ]))
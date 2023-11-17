from faststream.rabbit import RabbitQueue, RabbitExchange, ExchangeType

from src.config.settings import settings

telegram_exchange = RabbitExchange(settings.RABBITMQ.TELEGRAM_EXCHANGE, type=ExchangeType.DIRECT)

message_queue = RabbitQueue(
    name=settings.RABBITMQ.TELEGRAM_MESSAGE_QUEUE,
    exclusive=True
)

reply_to_message_queue = RabbitQueue(
    name=settings.RABBITMQ.TELEGRAM_REPLY_TO_MESSAGE_QUEUE,
    exclusive=True
)

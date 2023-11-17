from faststream.rabbit import RabbitBroker

from src.config.settings import settings

from .handlers import message, reply_to_message

broker = RabbitBroker(url=settings.RABBITMQ.URL.unicode_string())

broker.include_router(message.router)
broker.include_router(reply_to_message.router)

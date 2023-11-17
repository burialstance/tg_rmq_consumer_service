from pathlib import Path

from pydantic import AmqpDsn, PostgresDsn

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).parent.parent
_ENV_FILE = _BASE_DIR.parent.parent.joinpath('.env')


class RabbitMQ(BaseSettings):
    URL: AmqpDsn

    TELEGRAM_EXCHANGE: str = 'telegram'
    TELEGRAM_MESSAGE_QUEUE: str = 'message'
    TELEGRAM_REPLY_TO_MESSAGE_QUEUE: str = 'reply_to_message'


class Settings(BaseSettings):
    BASE_DIR: Path = _BASE_DIR
    DEBUG: bool = True
    APP_TITLE: str = 'Telegram Cryptobox Parser'
    APP_VERSION: str = '0.0.1'

    POSTGRES_URL: PostgresDsn
    RABBITMQ: RabbitMQ = RabbitMQ(_env_file=_ENV_FILE, _env_prefix='RABBITMQ_')

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra='ignore')


settings = Settings()

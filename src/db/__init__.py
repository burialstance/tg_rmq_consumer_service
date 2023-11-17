from functools import partial

from typing import Dict

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from tortoise import Tortoise, connections
from tortoise.exceptions import IntegrityError
from tortoise.log import logger

from src.config.settings import settings

TORTOISE_CONFIG = {
    'connections': {
        # 'default': {
        #     'engine': 'tortoise.backends.asyncpg',
        #     'credentials': {
        #         # 'host': settings.POSTGRES_HOST,
        #         'host': 'localhost',
        #         'port': settings.POSTGRES_PORT,
        #         'user': settings.POSTGRES_USER,
        #         'password': settings.POSTGRES_PASSWORD,
        #         'database': settings.POSTGRES_DB,
        #     }
        # }
        'default': settings.POSTGRES_URL.unicode_string()
    },
    'apps': {
        'telegram': {
            'models': ['src.models.telegram'],
        },
    },
    # 'routers': ['path.router1', 'path.router2'],
    'use_tz': True,
    # 'timezone': settings.TIMEZONE
}


def init_models(tortoise_config: Dict):
    try:
        apps_config: Dict = tortoise_config["apps"]
    except KeyError:
        raise Exception('Config must define "apps" section')

    for app_label, app_conf in apps_config.items():
        models = app_conf.get('models')
        Tortoise.init_models(models_paths=models, app_label=app_label)
        print(f'INIT MODELS {app_label}:{models}')


init_models(TORTOISE_CONFIG)


async def init_orm(generate_schemas: bool = False, drop_databases: bool = False):
    if drop_databases:
        await Tortoise.init(config=TORTOISE_CONFIG)
        await Tortoise._drop_databases()
        logger.info("Tortoise-ORM DROPPED ALL TABLES, %s, %s", connections._get_storage(), Tortoise.apps)

    await Tortoise.init(config=TORTOISE_CONFIG)
    logger.info("Tortoise-ORM started, %s, %s", connections._get_storage(), Tortoise.apps)

    if generate_schemas:
        logger.info("Tortoise-ORM generating schema")
        await Tortoise.generate_schemas()


async def close_orm():
    await connections.close_all()
    logger.info("Tortoise-ORM shutdown")


def register_database(
        app: FastAPI,
        generate_schemas: bool = False,
        drop_databases: bool = False
):
    # @app.on_event("startup")
    # async def init_orm_on_startup() -> None:
    #     await init_orm(generate_schemas=generate_schemas, drop_databases=drop_databases)
    app.add_event_handler('startup',
                          partial(init_orm, generate_schemas=generate_schemas, drop_databases=drop_databases))
    app.add_event_handler('shutdown', close_orm)

    @app.exception_handler(IntegrityError)
    async def integrityerror_exception_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=422,
            content={"detail": [{"loc": [], "msg": str(exc), "type": "IntegrityError"}]},
        )

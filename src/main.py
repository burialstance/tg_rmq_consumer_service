from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.config.logs import configure_logging
from src.config.settings import settings
from src.adapters.rabbitmq.broker import broker
from src.db import init_orm, close_orm
from src.admin import register_admin_app


@asynccontextmanager
async def fastapi_lifespan(app: FastAPI):
    register_admin_app(app)

    await init_orm(generate_schemas=True, drop_databases=False)
    await broker.start()

    yield

    await broker.close()
    await close_orm()


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=fastapi_lifespan
)
Instrumentator().instrument(app).expose(app)


@app.get('/healthcheck')
async def healthcheck():
    return 'ok'


configure_logging(20)

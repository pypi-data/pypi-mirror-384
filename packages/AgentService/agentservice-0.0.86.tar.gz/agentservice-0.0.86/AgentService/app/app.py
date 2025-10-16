
import fastapi
import uvicorn
from contextlib import asynccontextmanager

from AgentService.config import Config
from AgentService.types import setup_database

from .routes import (
    chat_router,
    storage_router
)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await setup_database(Config().db_uri, Config().db_name)

    yield

    return


app = fastapi.FastAPI()
app.include_router(chat_router)
app.include_router(storage_router)


def start_app():
    config = Config()
    uvicorn.run(app, host=config.app_host, port=config.app_port)

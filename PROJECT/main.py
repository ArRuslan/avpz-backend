from contextlib import asynccontextmanager
from pathlib import Path

from aerich import Command
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from . import config
from .routes import auth


@asynccontextmanager
async def migrate_and_connect_orm(app_: FastAPI):  # pragma: no cover
    if config.DB_CONNECTION_STRING != "sqlite://:memory:":
        migrations_dir = "data/migrations"

        command = Command({
            "connections": {"default": config.DB_CONNECTION_STRING},
            "apps": {"models": {"models": ["PROJECT.models", "aerich.models"], "default_connection": "default"}},
        }, location=migrations_dir)
        await command.init()
        if Path(migrations_dir).exists():
            await command.migrate()
            await command.upgrade(True)
        else:
            await command.init_db(True)
        await Tortoise.close_connections()

    async with RegisterTortoise(
            app=app_,
            db_url=config.DB_CONNECTION_STRING,
            modules={"models": ["PROJECT.models"]},
            generate_schemas=True,
    ):
        yield


app = FastAPI(lifespan=migrate_and_connect_orm)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)

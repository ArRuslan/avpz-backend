from contextlib import asynccontextmanager
from pathlib import Path

from aerich import Command
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from . import config
from .routes import auth, user, hotels, admin, rooms, bookings
from .utils.create_test_data import create_test_data
from .utils.multiple_errors_exception import MultipleErrorsException

try:
    import git
except ImportError:  # pragma: no cover
    git = None


@asynccontextmanager
async def migrate_and_connect_orm(app_: FastAPI):  # pragma: no cover
    if not config.IS_DEBUG:
        migrations_dir = "data/migrations"

        command = Command({
            "connections": {"default": config.DB_CONNECTION_STRING},
            "apps": {"models": {"models": ["hhb.models", "aerich.models"], "default_connection": "default"}},
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
            modules={"models": ["hhb.models"]},
            generate_schemas=True,
    ):
        if config.IS_DEBUG and not config.DONT_CREATE_TEST_DATA:
            await create_test_data()
        yield


app = FastAPI(
    lifespan=migrate_and_connect_orm,
    debug=config.IS_DEBUG,
    title="HHB" + ("-Debug" if config.IS_DEBUG else ""),
    openapi_url="/openapi.json" if config.IS_DEBUG else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=(["x-debug-token"] if config.IS_DEBUG else [])
)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(admin.router)


if config.IS_DEBUG:
    import fastapi.openapi.utils as fu
    from datetime import datetime
    from pytz import UTC

    fu.validation_error_response_definition = {
        "title": "HTTPValidationError",
        "type": "object",
        "properties": {
            "error": {
                "title": "Error messages",
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }

    time_fmt = "%d.%m.%Y %H:%M:%S"
    app.description = f"# Started at {datetime.now(UTC).strftime(time_fmt)} UTC"

    if git is not None:  # pragma: no cover
        repo = git.Repo(Path(__file__).parent.parent)
        last_commit = repo.head.commit
        last_commit_time = last_commit.committed_datetime.astimezone(UTC)
        app.description += f"\n# Git commit: {last_commit.hexsha[:8]}, {last_commit_time.strftime(time_fmt)}"

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    result = []
    for err in exc.errors():
        loc = ".".join(err["loc"][1:])
        if loc:
            loc = f"[{loc}] "
        result.append(f"{loc}{err['msg']}")

    return JSONResponse({
        "errors": result,
    }, status_code=422)


@app.exception_handler(MultipleErrorsException)
async def multiple_errors_exception_handler(_, exc: MultipleErrorsException) -> JSONResponse:
    return JSONResponse({
        "errors": exc.messages,
    }, status_code=exc.status_code)

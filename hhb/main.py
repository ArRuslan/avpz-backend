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
from .routes import auth, user, hotels
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
)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(hotels.router)


if config.IS_DEBUG:
    import fastapi.openapi.utils as fu
    from pathlib import Path

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

    if git is not None:  # pragma: no cover
        repo = git.Repo(Path(__file__).parent.parent)
        last_commit = repo.head.commit
        app.version = f"{last_commit.committed_datetime.strftime('%m.%d.%Y %H:%M:%S')}, {last_commit.hexsha[:8]}"

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

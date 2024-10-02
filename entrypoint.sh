#!/bin/bash

POETRY_VENV="$(poetry env info -p)"
export PATH="${PATH}:${POETRY_VENV}/bin"

#poetry run gunicorn ... --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --preload

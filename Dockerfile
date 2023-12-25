FROM python:3.12-slim as builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=1 \
    POETRY_CACHE_DIR=/root/.cache/pypoetry

RUN pip install poetry==1.7.1

WORKDIR /app
COPY pyproject.toml ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    touch README.md && poetry install --no-root --without=dev

FROM python:3.12-slim

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY despot ./despot

ENTRYPOINT ["python", "-m", "despot.cli"]

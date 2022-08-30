FROM python:3 as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 

RUN pip install poetry
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes | /venv/bin/pip install -r /dev/stdin

FROM base as final

COPY --from=builder /venv /venv
RUN mkdir instance
COPY docker-entrypoint-dev.sh ./
COPY tamagotchi ./tamagotchi

CMD [ "./docker-entrypoint-dev.sh" ]



FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app
USER app

COPY --chown=app:app pyproject.toml /app/pyproject.toml
COPY --chown=app:app taranis_base_bot /app/taranis_base_bot

ENV UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    GRANIAN_THREADS=2 \
    GRANIAN_WORKERS=2 \
    GRANIAN_BLOCKING_THREADS=4 \
    GRANIAN_INTERFACE=wsgi \
    GRANIAN_HOST=0.0.0.0

RUN uv venv && . /app/.venv/bin/activate && uv sync --frozen

EXPOSE 8000
CMD ["granian", "taranis_base_bot.app"]

FROM ghcr.io/astral-sh/uv:python3.13-alpine

LABEL description="Code-Reminder aggregation tool"

WORKDIR /app

RUN addgroup -S app && \
    adduser -S -G app app

RUN apk add --no-cache git

ENV PATH=/app/.venv/bin:$PATH

COPY . /app

RUN chown -R app:app /app

USER app

RUN uv sync --locked --no-dev

ENTRYPOINT ["reminder-aggregator", "report"]

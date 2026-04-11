# ---------------------------------------------------------------- BUILDER IMAGE
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# ---------------------------------------------------------------- RUNTIME IMAGE
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS runtime

ENV UV_NO_SYNC=1

WORKDIR /app

COPY --from=builder --chown=musicbot:musicbot /app /app

ARG UID=10001
ARG GID=10001
RUN groupadd -g $GID musicbot && useradd -m -u $UID -g $GID musicbot
RUN mkdir -p /app/logs /app/data && chown -R musicbot:musicbot /app/logs /app/data
USER musicbot

ENTRYPOINT ["uv", "run"]
CMD ["musicbot"]

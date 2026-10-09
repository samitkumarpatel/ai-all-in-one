# Small Python image (Alpine) with uv installing the exact versions from uv.lock
FROM python:3.14-alpine

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

# Dependencies first, so code changes don't reinstall them
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

CMD ["python", "server.py"]

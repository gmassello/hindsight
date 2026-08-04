FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
RUN uv tool install mcp-server-datahub
ENV PATH="/root/.local/bin:$PATH"
COPY src ./src
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD [".venv/bin/hindsight", "serve", "--host", "0.0.0.0"]

# Image that RUNS the recipe manager (not a development environment).
#   docker build -t recipes .
#   docker run --rm recipes show data/recipes.json

# Stage 1: install the project into a virtual environment with uv.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project
COPY src ./src
RUN uv sync --locked --no-editable

# Stage 2: only the environment and the sample data, no uv, no build tools.
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY data ./data
ENV PATH="/app/.venv/bin:$PATH"
RUN useradd --create-home recipes
USER recipes
ENTRYPOINT ["recipes"]
CMD ["--help"]

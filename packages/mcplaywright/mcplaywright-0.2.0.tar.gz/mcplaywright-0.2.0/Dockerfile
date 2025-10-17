# Multi-stage build for MCPlaywright with uv
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim as base

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Development stage with hot-reload capabilities
FROM base as dev

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies with dev extras
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --dev --frozen

# Copy source code for development
COPY . .

# Install Playwright browsers
RUN uv run playwright install chromium firefox webkit
RUN uv run playwright install-deps

# Enable hot-reload and development features
ENV PYTHONPATH=/app/src
ENV DEVELOPMENT_MODE=true
ENV HOT_RELOAD=true
ENV UV_COMPILE_BYTECODE=0

EXPOSE 8000

# Development command with hot-reload
CMD ["uv", "run", "python", "-m", "mcplaywright.server", "--reload"]

# Production stage with optimized build
FROM base as prod

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install production dependencies only
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# Copy source code
COPY . .

# Install Playwright browsers for production
RUN uv run playwright install chromium firefox webkit
RUN uv run playwright install-deps

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcplaywright && \
    chown -R mcplaywright:mcplaywright /app
USER mcplaywright

# Create directories with proper permissions
RUN mkdir -p /app/artifacts /app/data /app/logs && \
    chmod 755 /app/artifacts /app/data /app/logs

# Enable bytecode compilation for production performance
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONPATH=/app/src
ENV DEVELOPMENT_MODE=false

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uv", "run", "python", "-m", "mcplaywright.server"]

# Default target is production
FROM prod as default
# EpitopeRank-ESM2 Docker Image
# Based on Debian slim (glibc) so numpy/scipy/matplotlib/pillow use official
# prebuilt manylinux wheels on both linux/amd64 and linux/arm64.

FROM python:3.11-slim AS builder

WORKDIR /build

# pip 源做成构建参数：默认保持国内镜像（本地构建快），
# CI/海外环境用 --build-arg PIP_INDEX_URL=https://pypi.org/simple 覆盖。
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --index-url "$PIP_INDEX_URL" --prefix=/install -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EPITOPERANK_RUNTIME_ROOT=/data/runtime \
    EPITOPERANK_MEMORY_DB=/data/epitoperank.sqlite3 \
    EPITOPERANK_LITERATURE_DB=/data/literature.sqlite3

# Install minimal runtime libraries (OpenMP + font/image libs for matplotlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libfreetype6 \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r epitoperank && useradd -r -g epitoperank -m epitoperank

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create data directory and set permissions
RUN mkdir -p /data && chown -R epitoperank:epitoperank /data /app

# Expose port (the web UI is rendered by the API at `/`)
EXPOSE 8800

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8800/api/health')" || exit 1

# Switch to non-root user
USER epitoperank

# Default command
CMD ["python", "run.py", "serve", "--api", "--ui", "--port", "8800"]

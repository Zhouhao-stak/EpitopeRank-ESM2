# EpitopeRank Docker Image
# Based on Alpine for minimal size and reliable package management

FROM python:3.11-alpine AS builder

WORKDIR /build

# pip 源做成构建参数：默认保持国内镜像（本地构建快），
# CI/海外环境用 --build-arg PIP_INDEX_URL=https://pypi.org/simple 覆盖。
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Install build dependencies (Alpine uses apk, much faster than apt)
# Added rust compiler for gseapy which requires it for building from source
RUN apk add --no-cache gcc g++ musl-dev rust cargo

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --index-url "$PIP_INDEX_URL" --prefix=/install -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-alpine AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EPITOPERANK_RUNTIME_ROOT=/data/runtime \
    EPITOPERANK_MEMORY_DB=/data/epitoperank.sqlite3 \
    EPITOPERANK_LITERATURE_DB=/data/literature.sqlite3

# Install runtime dependencies (libgomp for OpenMP support)
RUN apk add --no-cache libgomp

# Create non-root user
RUN addgroup -S epitoperank && adduser -S epitoperank -G epitoperank

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

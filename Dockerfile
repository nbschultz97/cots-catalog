FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip build && \
    python -m build --wheel

FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="architect-companion-mcp"
LABEL org.opencontainers.image.description="Offline-first MCP server for COTS sUAS / FPV build planning"
LABEL org.opencontainers.image.source="https://github.com/nbschultz97/cots-catalog"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install the wheel built in the builder stage. mcp pulls in its
# transitive deps; we keep the runtime image lean by not installing
# dev extras.
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Bundle the public hobby data pack
COPY data /app/data
ENV ARCHITECT_DATA_DIR=/app/data
ENV ARCHITECT_COMPANION_DATA_DIR=/app/runtime_data

# Non-root user for container hardening
RUN useradd --create-home --uid 1000 architect && \
    mkdir -p /app/runtime_data && \
    chown -R architect:architect /app
USER architect

# stdio MCP server — connect with a host that pipes stdin/stdout
ENTRYPOINT ["architect-companion-mcp"]

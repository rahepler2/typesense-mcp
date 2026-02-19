FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --shell /bin/sh mcp

COPY --from=builder /install /usr/local
WORKDIR /app
COPY . .

USER mcp

ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/mcp')" || exit 1

ENTRYPOINT ["python", "main.py"]

# Quickstart

## Install

```bash
pip install architect-companion-mcp
```

Or from source:

```bash
git clone https://github.com/nbschultz97/cots-catalog.git
cd cots-catalog
pip install -e ".[dev]"
```

## Verify

```bash
architect-companion-mcp --version
architect-companion-mcp --list-tools
architect-companion-mcp --diagnostics
```

You should see version 0.8.0+, 11 tools listed, and a diagnostics
report showing the catalog passes validation.

## Run the MCP server

```bash
architect-companion-mcp
```

The server blocks on stdio. Connect from your MCP host (Claude Desktop,
Claude Code, Cursor, etc.) — see [Integration](integration.md).

## Try the examples

```bash
python examples/recommend_first_build.py
python examples/check_my_5in.py
python examples/long_range_endurance.py
python examples/ingest_walkthrough.py
```

## Run via Docker

```bash
docker run --rm -i ghcr.io/nbschultz97/architect-companion-mcp:latest
```

The container ships the bundled hobby data pack. Mount your own catalog
at `/app/data` if you want to override:

```bash
docker run --rm -i \
  -v $(pwd)/my-catalog:/app/data \
  ghcr.io/nbschultz97/architect-companion-mcp:latest
```

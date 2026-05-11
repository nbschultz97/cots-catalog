# Examples

Runnable scripts demonstrating how to call the MCP server's tool
functions directly (no MCP client required). Each one is meant to be
read top-to-bottom — they're documentation by example.

```bash
pip install -e .
python examples/recommend_first_build.py
python examples/check_my_5in.py
python examples/long_range_endurance.py
python examples/ingest_walkthrough.py
```

The same functions these scripts call are what get exposed over stdio
when you run `architect-companion-mcp` and connect from Claude Desktop
or Claude Code.

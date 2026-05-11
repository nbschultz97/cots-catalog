# Architect Companion MCP

Offline-first **Model Context Protocol (MCP) server** for COTS sUAS / FPV
build planning. LLM clients (Claude Desktop, Claude Code, Cursor, any
MCP host) get a curated, manufacturer-sourced parts library and a set
of compatibility, endurance, and blueprint tools.

The catalog is **hobby / commercial sUAS only**. No military framing,
no export-controlled parts, no operationally sensitive data.

[Quickstart →](quickstart.md){ .md-button .md-button--primary }
[GitHub →](https://github.com/nbschultz97/cots-catalog){ .md-button }

## What you get

- **11 stdio MCP tools** over the parts library, compatibility engine,
  physics model, and recommender.
- **7 MCP Resources** (`catalog://...`, `schema://...`) the LLM browses
  without tool calls.
- **5 MCP Prompts** for templated workflows (design build, compare,
  troubleshoot, what-if endurance, upgrade path).
- **100+ parts** across 8 categories with full `data_source`
  provenance — manufacturer URL and fetch timestamp on every entry.
- **7 mission presets** spanning tinywhoop indoor to multi-day
  endurance survey.
- **Real physics** — BEM-induced power × empirical aero loss multiplier
  for multirotor; Breguet with empirical L/D-eta for fixed-wing. Honest
  ±25-35% accuracy.
- **JSON Schema validation** on catalog load.
- **No network calls anywhere in the package.** Air-gap friendly.

## Architecture at a glance

```
+----------------+        stdio MCP        +-----------------------+
| Claude Desktop |  <------------------>   | architect-companion-  |
| Claude Code    |                          |        mcp           |
| Cursor (any)   |                          |                       |
+----------------+                          |  tools: 11            |
                                            |  resources: 7         |
                                            |  prompts: 5           |
                                            +-----------+-----------+
                                                        |
                                                        v
                                            +-----------------------+
                                            | data/                 |
                                            |  parts_library.json   |
                                            |  preset_*.json (7)    |
                                            |  schema/*.json        |
                                            +-----------------------+
```

## License

MIT — see [LICENSE](https://github.com/nbschultz97/cots-catalog/blob/main/LICENSE).

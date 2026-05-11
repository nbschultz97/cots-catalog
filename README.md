# Architect Companion MCP

Offline-first **MCP server for COTS robotics mission planning**, complementing the
[Ceradon Architect](https://ceradonsystems.com) suite (COTS-Architect). Exposes
the parts library, presets, and engineering checks as stdio MCP tools so LLM
clients (Claude Desktop, Claude Code, Cursor, etc.) can do sUAS mission planning
against real catalog data.

## Scope

- 8 stdio MCP tools over the bundled COTS-Architect parts library (v1.1.0
  schema) and MissionProject schema (v2.0.0).
- No network calls, no cloud, no hardware required. Bundled `data/`
  directory carries everything needed.
- Sanity-check math only — voltage chain, weight budget, RF-band overlap,
  hover-endurance approximation. **Not a flight simulator.**

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate              # PowerShell
pip install -e .
architect-companion-mcp             # blocks on stdio, ready to be wired into an MCP client
```

Run the tests:

```bash
pip install pytest
python -m pytest -q
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `health` | Server status, version, data dir, catalog counts, available presets and operation types |
| `list_components` | Browse the parts catalog with filters (category, tag, manufacturer, availability, max_weight_g, max_cost_usd, frequency_band, limit) |
| `get_part` | Fetch a single part by its catalog ID |
| `check_compatibility` | Voltage chain, weight budget vs airframe payload, RF-band overlap, ESC vs motor current |
| `generate_mission_blueprint` | Produce a `MissionProject v2` stub seeded from one of the bundled presets |
| `estimate_flight_time` | Hover endurance approximation — pass catalog IDs or raw battery/airframe numbers |
| `recommend_configuration` | Heuristic kit pick for a compute tier + mission type, ranked by availability/tag-match/cost |
| `record_observation` | Append-only JSONL telemetry log to local storage |

### Categories

`airframes`, `motors`, `escs`, `batteries`, `flight_controllers`, `radios`,
`sensors`, `accessories`.

### Operation types

`recon`, `mesh_recon`, `low_infrastructure`, `sustainment`,
`partner_sustainment`, `urban_lane`, `urban_high_ew`, `winter`,
`cold_weather`.

### Compute tiers

`pi-zero`, `pi4`, `pi5`, `jetson-nano`, `jetson-orin-nano`, `x86`.

## Data directory

The server reads JSON from `data/` (bundled in this repo, vendored from
COTS-Architect). Override with `ARCHITECT_DATA_DIR`:

```powershell
$env:ARCHITECT_DATA_DIR = "C:\Users\noah\COTS-Architect\data"
architect-companion-mcp
```

JSONL telemetry from `record_observation` lands in
`ARCHITECT_COMPANION_DATA_DIR` (defaults to `./runtime_data`).

## Wiring into Claude Desktop

Add this to `claude_desktop_config.json` (Windows path:
`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp",
      "env": {
        "ARCHITECT_DATA_DIR": "C:\\Users\\noah\\cots-catalog\\data",
        "ARCHITECT_COMPANION_DATA_DIR": "C:\\Users\\noah\\cots-catalog\\runtime_data"
      }
    }
  }
}
```

For Claude Code, add to `.claude/settings.json` or your global settings:

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp"
    }
  }
}
```

Restart the client; the tools appear under the `architect-companion` server.

## Edge deployment notes

- Python 3.9+. Tested on 3.12. Targets Raspberry Pi 4/5 and Jetson Orin Nano.
- JSONL persistence — no database stack to pull in air-gapped builds.
- All tools operate fully offline; no network calls anywhere in the package.

## Out of scope (intentionally)

- Live sync with COTS-Architect (just re-vendor `data/`).
- Mesh routing / link-budget compute — defer to MissionProject planner.
- Cost roll-ups beyond per-part sums.
- Regulatory / airspace / NOTAM checks.
- Flight simulation. The endurance tool is a single-line approximation.

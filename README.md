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

`long_range`, `long_range_relay`, `relay`, `endurance`, `endurance_survey`,
`survey`, `mapping`, `urban`, `urban_congested`, `race`, `racing`,
`cold_weather`, `winter`. Unknown types fall back to `long_range_relay`.

### Mission types (recommend_configuration)

`long_range`, `endurance_survey`, `freestyle`, `racing`, `cinematic`,
`cold_weather`. Unknown types fall back to `long_range`.

### Compute tiers

`pi-zero`, `pi4`, `pi5`, `jetson-nano`, `jetson-orin-nano`, `x86`.

### Bring your own catalog

The bundled `data/` directory is a hobby / COTS FPV reference pack you
can use out of the box. Point `ARCHITECT_DATA_DIR` at a different
directory to swap in your own parts library and presets — useful for
race clubs, mapping shops, fleet operators, or anyone running an
internal inventory.

### Adding parts: the `architect-companion-ingest` CLI

A second console script ships alongside the MCP server for growing the
catalog from manufacturer product pages:

```bash
architect-companion-ingest https://radiomasterrc.com/products/rp1-expresslrs-2-4ghz-nano-receiver
```

The ingester tries three strategies in order:

1. **JSON-LD Product schema** — clean structured extraction (Shopify
   stores generally publish this).
2. **OpenGraph meta tags** — falls back when JSON-LD is missing.
3. **`from_specs()` programmatic call** — for pages without either,
   import the module and pass a hand-curated spec dict.

Every ingested entry carries a `data_source: {url, fetched_at, parser}`
block so the catalog stays auditable. The `_extraction.missing_fields`
list tells you what the parser couldn't get; fill those in by hand
before merging into `data/parts_library.json`.

**ToS note:** the ingester is meant for manufacturer pages (iFlight,
T-Motor, EMAX, Lumenier, Happymodel, RadioMaster, BetaFPV, etc.) where
spec data is intended to be public. Don't point it at retailers whose
terms forbid automated access.

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

## Known limitations

What the compatibility engine **does** catch:

- Battery nominal voltage outside an ESC / FC / motor voltage range.
- Total component weight exceeding the airframe payload budget (only as
  accurate as the catalog's `max_payload_g`).
- Airframe motor_count not matching the number of motor entries (≥2 entries
  treated as explicit per-rotor listing; one entry treated as a spec line).
- ESC count vs motors — flags missing 4-in-1 or wrong single-ESC count.
- Motor KV outside the rough band for the airframe's prop size
  (heuristic FPV builder rule of thumb, not a thrust model).
- Control vs video radio frequency-band overlap.
- ESC max current below motor peak current.

What it **does not** catch:

- Mount-hole pattern mismatch (30.5×30.5 vs 20×20 stacks).
- Battery C-rating vs sustained current draw — only validates peak.
- Frame battery-bay dimensions vs battery dimensions.
- Antenna polarization (RHCP vs LHCP) between TX and RX.
- VTX output power legality for the operator's regulatory region.
- Goggle compatibility with VTX (Analog ↔ Walksnail ↔ DJI ↔ HDZero).
- Actual thrust headroom or hover stability — see endurance disclaimer.

The endurance tool (`estimate_flight_time`) is a single-line hover
approximation. Forward-flight efficiency on long-range and fixed-wing
platforms can produce 1.5–2× longer real endurance than the tool
reports. Use as a sanity check, not a published spec.

## Out of scope (intentionally)

- Live sync with COTS-Architect (just re-vendor `data/`).
- Mesh routing / link-budget compute — defer to MissionProject planner.
- Cost roll-ups beyond per-part sums.
- Regulatory / airspace / NOTAM checks.
- Flight simulation.

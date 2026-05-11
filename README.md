# Architect Companion MCP

[![CI](https://github.com/nbschultz97/cots-catalog/actions/workflows/ci.yml/badge.svg)](https://github.com/nbschultz97/cots-catalog/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-purple.svg)](https://modelcontextprotocol.io/)

Offline-first **Model Context Protocol (MCP) server for COTS sUAS / FPV
build planning**. Exposes a curated, manufacturer-sourced parts library
and a set of compatibility / endurance / blueprint tools so LLM clients
(Claude Desktop, Claude Code, Cursor, any MCP host) can recommend
builds, sanity-check them, and emit MissionProject v2 stubs — all from
local data, no cloud calls.

**The catalog is hobby / commercial sUAS only.** No military framing,
no export-controlled parts, no operationally sensitive data.

---

## Table of contents

- [What you get](#what-you-get)
- [Quickstart](#quickstart)
- [MCP tools](#mcp-tools)
- [Wiring into Claude Desktop / Claude Code](#wiring-into-claude-desktop--claude-code)
- [CLI tools](#cli-tools)
- [Categories, operation types, compute tiers](#categories-operation-types-compute-tiers)
- [Bring your own catalog](#bring-your-own-catalog)
- [Adding parts](#adding-parts)
- [Examples](#examples)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)
- [License](#license)

---

## What you get

- **10 stdio MCP tools** over a manufacturer-sourced parts library.
- **80+ COTS parts** across 8 categories (airframes, motors, ESCs,
  batteries, flight controllers, radios, sensors, accessories) sourced
  from iFlight, EMAX, T-Motor, RadioMaster, BetaFPV, GEPRC, Holybro,
  Walksnail, DJI, Tattu, GAONENG, CNHL, Lumenier, Diatone, Happymodel.
  Every part carries `data_source` provenance.
- **7 mission presets** covering long-range relay, endurance survey,
  urban congested-RF, cold-weather, tinywhoop indoor, sub-250g, and
  beginner 5". Each conforms to the MissionProject v2 schema.
- **Self-validating recommender** — calls `check_compatibility` on its
  own picks so the LLM doesn't have to remember.
- **JSON Schema validation** of the catalog on load (optional dependency).
- **Auditable provenance** — every ingested part has `data_source.url`
  and `data_source.fetched_at`.
- **No network calls anywhere in the package.** Air-gap friendly.

---

## Quickstart

```bash
# Install
pip install -e .

# Run the MCP server (blocks on stdio, ready for a client)
architect-companion-mcp

# Or just check it works
architect-companion-mcp --version
architect-companion-mcp --list-tools
architect-companion-mcp --diagnostics
```

Run the tests:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

---

## MCP tools

| Tool | Description |
|------|-------------|
| `health` | Server status, version, data dir, catalog counts, available presets and operation types |
| `list_components` | Browse the parts catalog with filters (category, tag, manufacturer, availability, max_weight_g, max_cost_usd, frequency_band, limit) |
| `get_part` | Fetch a single part by its catalog ID |
| `check_compatibility` | Voltage chain, weight budget, mount patterns, motor count / ESC count, KV vs prop, RF-band overlap, ESC vs motor current |
| `generate_mission_blueprint` | Produce a `MissionProject v2` stub seeded from one of the bundled presets |
| `estimate_flight_time` | Hover endurance approximation — pass catalog IDs or raw battery / airframe numbers |
| `recommend_configuration` | Heuristic kit pick for a compute tier + mission type, **self-validates** via `check_compatibility` |
| `validate_catalog` | Run JSON Schema + uniqueness + required-field checks on the currently loaded library (useful with `ARCHITECT_DATA_DIR`) |
| `record_observation` | Append-only JSONL telemetry log to local storage |

The recommender's output now includes a `validation` block with
`compatible`, `issues`, and `budget` — so the LLM client immediately
knows whether the picks pass engineering checks.

---

## Wiring into Claude Desktop / Claude Code

### Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp"
    }
  }
}
```

### Claude Code

`.claude/settings.json` (project) or `~/.claude/settings.json` (global):

```json
{
  "mcpServers": {
    "architect-companion": {
      "command": "architect-companion-mcp"
    }
  }
}
```

Restart the client. The tools appear under the `architect-companion`
server.

---

## CLI tools

Two console scripts ship with the package:

| Command | What it does |
|---------|--------------|
| `architect-companion-mcp` | Run the MCP server (stdio). Supports `--version`, `--list-tools`, `--diagnostics`. |
| `architect-companion-ingest <url>` | Pull a manufacturer product page through the ingester and print the resulting part dict to stdout. JSON-LD → OpenGraph → spec dict fallback. |

---

## Categories, operation types, compute tiers

**Part categories:** `airframes`, `motors`, `escs`, `batteries`,
`flight_controllers`, `radios`, `sensors`, `accessories`.

**Operation types (for `generate_mission_blueprint`):**
`long_range`, `long_range_relay`, `relay`, `endurance`,
`endurance_survey`, `survey`, `mapping`, `urban`, `urban_congested`,
`race`, `racing`, `cold_weather`, `winter`, `tinywhoop`,
`tinywhoop_indoor`, `indoor`, `sub_250g`, `recreational`,
`beginner`, `beginner_5in`, `first_build`. Unknown types fall back to
`long_range_relay`.

**Mission types (for `recommend_configuration`):** `long_range`,
`endurance_survey`, `freestyle`, `racing`, `cinematic`, `cold_weather`.

**Compute tiers:** `pi-zero`, `pi4`, `pi5`, `jetson-nano`,
`jetson-orin-nano`, `x86`. Heavier tiers bias the airframe pick toward
larger frames with payload room for the companion compute.

---

## Bring your own catalog

The bundled `data/` directory is a hobby / COTS FPV reference pack you
can use out of the box. Point `ARCHITECT_DATA_DIR` at a different
directory to swap in your own parts library and presets:

```bash
export ARCHITECT_DATA_DIR=/path/to/my-catalog
architect-companion-mcp
```

Your custom catalog must conform to the schemas in `data/schema/`. The
`validate_catalog` MCP tool will tell you exactly what's wrong if a
load fails.

JSONL telemetry from `record_observation` lands in
`ARCHITECT_COMPANION_DATA_DIR` (defaults to `./runtime_data`).

---

## Adding parts

```bash
architect-companion-ingest https://radiomasterrc.com/products/rp1-expresslrs-2-4ghz-nano-receiver
```

Three parsers, tried in order:

1. **JSON-LD Product schema** — clean structured extraction. Most
   Shopify stores ship this.
2. **OpenGraph meta tags** — falls back when JSON-LD is missing.
3. **`from_specs()`** — for pages without either, import the module and
   pass a hand-curated spec dict directly.

Every ingested entry carries `data_source: {url, fetched_at, parser}`
so the catalog stays auditable. `_extraction.missing_fields` tells you
what the parser couldn't get; fill those by hand before merging into
`data/parts_library.json`.

**ToS:** target manufacturer pages, not retailers. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the full process.

---

## Examples

Runnable scripts in [`examples/`](examples/):

- `recommend_first_build.py` — pick a long-range 7" kit and show the
  self-validation report.
- `check_my_5in.py` — run compatibility checks against a hand-picked
  5" build manifest.
- `long_range_endurance.py` — compare hover endurance across all
  airframes in the catalog.
- `ingest_walkthrough.py` — both ingester paths end-to-end.

---

## Known limitations

What the compatibility engine **does** catch:

- Battery nominal voltage outside an ESC / FC / motor voltage range.
- Total component weight exceeding the airframe payload budget (only as
  accurate as the catalog's `max_payload_g`).
- Airframe motor_count not matching the number of motor entries (≥2
  entries treated as explicit per-rotor listing; one entry treated as a
  spec line).
- ESC count vs motors — flags missing 4-in-1 or wrong single-ESC count.
- Motor KV outside the rough band for the airframe's prop size
  (heuristic FPV builder rule of thumb).
- Motor / FC / airframe mount-hole pattern mismatch.
- Control vs video radio frequency-band overlap.
- ESC max current below motor peak current.

What it **does not** catch:

- Battery C-rating vs sustained (not peak) current draw.
- Frame battery-bay dimensions vs battery dimensions.
- Antenna polarization (RHCP vs LHCP) between TX and RX.
- VTX output power legality for the operator's regulatory region.
- Goggle compatibility with VTX (Analog ↔ Walksnail ↔ DJI ↔ HDZero).
- Actual thrust headroom or hover stability — see endurance disclaimer.

The endurance tool is a single-line hover approximation. Forward-flight
efficiency on long-range and fixed-wing platforms can produce 1.5–2×
longer real endurance than the tool reports. Use as a sanity check,
not a published spec.

---

## Contributing

We welcome PRs that add parts, compatibility rules, presets, and
examples. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process,
including data-source expectations and the hobby-marketable scope.

Security reports: see [SECURITY.md](SECURITY.md).
Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Out of scope (intentionally)

- Live sync with COTS-Architect (just re-vendor `data/`).
- Mesh routing / link-budget compute — defer to MissionProject planner.
- Cost roll-ups beyond per-part sums.
- Regulatory / airspace / NOTAM checks.
- Flight simulation.

---

## License

MIT — see [LICENSE](LICENSE).

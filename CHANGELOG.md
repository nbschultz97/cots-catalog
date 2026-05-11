# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] — 2026-05-11

### Added — physics
- **Real cruise-aware physics.** Replaced hover-only one-liner with:
  - BEM-induced power × empirical aero-loss multiplier (multirotor hover).
  - Airframe-class cruise factor (multirotor cruise).
  - Simplified Breguet with empirical L/D-eta (fixed-wing cruise).
  - ISA air density model (altitude-aware).
  - Class-aware component overhead so AUW reflects buildable quads, not just airframe + battery.
- New `estimate_thrust(airframe, motor, battery)` tool — per-motor / total
  thrust + T/W ratio with verdict (race / freestyle / cruise / marginal).
- New `estimate_range_km(airframe, battery, cruise_speed)` tool — one-way
  and round-trip range with a planning factor caveat.
- Calibrated against published FPV community flight times. Honest
  accuracy band: ±25% hover, ±35% multirotor cruise, ±40% fixed-wing.

### Added — MCP-native ergonomics
- **MCP Resources** (read-only URIs the LLM browses without tool calls):
  `catalog://stats`, `catalog://categories/{category}`,
  `catalog://parts/{part_id}`, `catalog://presets`,
  `catalog://presets/{filename}`, `schema://parts_library`,
  `schema://mission_project`.
- **MCP Prompts** (templated workflows / slash-commands):
  `design_build`, `compare_builds`, `troubleshoot_build`,
  `endurance_what_if`, `upgrade_path`.

### Added — distribution
- PyPI release GitHub Action (trusted publishing on tag push).
- Multi-arch Dockerfile (linux/amd64 + linux/arm64) published to GHCR.
- mkdocs Material site scaffold + GitHub Pages deploy workflow.
- Docs pages: home, quickstart, integration, tools reference,
  resources reference, prompts reference, catalog overview, ingest
  guide, BYO data pack, compatibility rules, physics model,
  limitations.

### Catalog totals
- 11 tools (was 10) + 7 resources + 5 prompts.
- 100 parts across 8 categories.
- 7 mission presets.
- 47 pytest tests, all passing.

## [0.7.0] — 2026-05-11

### Catalog
- **Hit 100-part milestone** (81 → 100, +19 manufacturer-sourced).
- 2 new airframes: BetaFPV Pavo Pico II (sub-100g 1.6" cinewhoop), iFlight
  Nazgul Evoque F5 V3 (5" DC/X switchable freestyle frame).
- 2 new motors: T-Motor Velox V2207 V3 1950KV, iFlight XING 2806.5 1300KV
  Cinelifter (7-8" long-range).
- 2 new ESCs: Hobbywing XRotor Micro 60A 4-in-1, HGLRC SPECTER 60A 4-in-1.
- 2 new flight controllers: Matek H743-SLIM V4 (ArduPilot / INAV / fixed-wing),
  SpeedyBee F405 V4 BLS 55A AIO.
- 2 new batteries: CNHL Black Series 4S 1500mAh 100C, GAONENG GNB 1S 450mAh
  HV (tinywhoop).
- 4 new radios: TBS Crossfire Nano RX (915/868MHz LoRa long-range),
  Happymodel EP1 TCXO ELRS RX, RadioMaster Boxer ELRS TX, TBS Tango 2 Pro
  Crossfire TX.
- 3 new sensors: Foxeer Razer Mini 1200TVL analog camera, RunCam Phoenix 2 SP
  Starlight, Caddx Vista DJI Digital HD VTX.
- 2 new accessories: HQProp Ethix S5 5x4x3 propeller, TrueRC X²-AIR 5.8 MK II
  patch antenna (RHCP/LHCP).
- Every new entry carries `data_source.url + fetched_at + parser` provenance.

## [0.6.0] — 2026-05-11

### Added
- MIT LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md.
- GitHub Actions CI: pytest matrix across Python 3.9-3.13 + lint + schema validation.
- Issue and PR templates.
- JSON Schema validation on catalog load (optional `jsonschema` extra).
- `tests/test_catalog_quality.py` — every part must have required fields and unique ID.
- Recommender self-validates picks via `check_compatibility`; surfaces issues in output.
- Mount-hole pattern compatibility rule (motor vs FC vs airframe).
- MCP CLI gains `--version`, `--list-tools`, `--diagnostics` flags.
- New presets: `preset_tinywhoop_indoor`, `preset_sub_250g`, `preset_beginner_5in`.
- `examples/` directory with 4 runnable scripts.
- README badges + table of contents.

### Changed
- `recommend_configuration` output includes `validation` block with `compatible`,
  `issues`, and (optionally) suggested alternatives.

### Catalog
- ~10-15 new ingested parts targeting tinywhoop motors, 4-in-1 ESCs, HD VTXes,
  ELRS TX modules. Catalog growth: 73 → ~85 parts.

## [0.5.0] — 2026-05-11

### Added
- `architect_companion_mcp.ingest` module: stdlib-only URL → part dict parser.
  Three strategies: JSON-LD Product schema → OpenGraph meta tags →
  `from_specs()` for hand-curated dicts.
- `architect-companion-ingest <url>` CLI.
- Every ingested part carries `data_source: {url, fetched_at, parser}` provenance.
- 9 new tests for the ingester.

### Catalog
- 10 new manufacturer-sourced parts (iFlight XING2 motors, EMAX ECO II 2400KV,
  T-Motor F40 PRO V, RadioMaster RP1 V2 / XR1 / ER6, Holybro Kakute H7 V2,
  GAONENG GNB 6S, CNHL Black 6S). Catalog: 63 → 73.

## [0.4.1] — 2026-05-11

### Fixed
- `compute_tier` parameter on `recommend_configuration` was previously a no-op.
  Now actually filters airframes by payload budget and biases tag preferences.
- Pi-zero now lands on a 5" frame; Jetson Orin lands on a flying-wing.

### Added
- Compatibility engine: motor_count cross-check, ESC count vs motor count check,
  KV vs prop-size sanity check (four prop-size bands).
- README "Known limitations" section documenting what the engine catches and
  doesn't.

## [0.4.0] — 2026-05-11

### Changed (BREAKING — public posture scrub)
- Removed ITAR/EAR thermal sensor entry.
- Stripped "ISR" from parts library (IDs, tags, notes → "heavy-lift" /
  "mapping" / "cinematography").
- Dropped EMCON / operator-drone framing from catalog description.
- Replaced 4 mil-flavored presets with hobby equivalents
  (`long_range_relay`, `endurance_survey`, `urban_congested`, `cold_weather`).
- `environment_taxonomy`: `ewLevels` → `rfEnvironments`.
- `parts_library_schema`: dropped `nsn` field.
- `mission_project_schema_v2`: `ew_profile` → `rf_environment`.
- `recommend_configuration`: dropped `strike` / `sustainment` mission types in
  favor of `freestyle` / `racing` / `cinematic` / `long_range` / `endurance_survey` /
  `cold_weather`.

## [0.3.0] — 2026-05-11

### Added
- First real release: 8 stdio MCP tools (`health`, `list_components`, `get_part`,
  `check_compatibility`, `generate_mission_blueprint`, `estimate_flight_time`,
  `recommend_configuration`, `record_observation`).
- Bundled COTS-Architect parts library (63 parts, 8 categories) and 4 mission
  presets.
- 18 pytest tests covering every tool.
- README with Claude Desktop and Claude Code config snippets.

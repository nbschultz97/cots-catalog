# Tools reference

11 stdio MCP tools.

| Tool | Description |
|------|-------------|
| `health` | Server status, version, data dir, catalog counts |
| `list_components` | Browse the parts catalog with filters |
| `get_part` | Fetch a single part by ID |
| `check_compatibility` | Voltage chain, weight, mount, KV/prop, RF, ESC current |
| `generate_mission_blueprint` | MissionProject v2 stub from a preset |
| `estimate_flight_time` | BEM hover + cruise factor (multirotor) / Breguet (FW) |
| `estimate_thrust` | Per-motor and total thrust + T/W ratio + verdict |
| `estimate_range_km` | One-way / round-trip range at a cruise speed |
| `recommend_configuration` | Self-validating kit pick for compute_tier × mission |
| `validate_catalog` | JSON Schema + uniqueness + required-field validation |
| `record_observation` | JSONL telemetry append |

See [Resources](resources.md) and [Prompts](prompts.md) for the read-only
URIs and templated workflows.

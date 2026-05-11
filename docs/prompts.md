# Prompts reference

MCP Prompts are templated workflows the user invokes by slash command
in their MCP host (Claude Desktop shows them as `/architect-companion__*`).

| Prompt | Arguments | What it does |
|--------|-----------|--------------|
| `design_build` | mission, budget_usd, compute_tier, skill | Recommend → validate → swap → final report |
| `compare_builds` | build_a_ids, build_b_ids | Side-by-side A/B comparison across cost, AUW, T/W, endurance |
| `troubleshoot_build` | part_ids, symptom | Map symptom to likely causes via compat + physics |
| `endurance_what_if` | airframe_id, battery_id, payload_weight_g | Vary payload, compare batteries, compute range |
| `upgrade_path` | current_build_ids, goal | Three-tier upgrade-swap recommendations |

Each prompt expands into a structured set of instructions the LLM
follows using the server's tools — you don't write the workflow, the
prompt does.

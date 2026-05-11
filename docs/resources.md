# Resources reference

Read-only MCP Resources let the LLM browse the catalog without spending
tool calls.

| URI | What it returns |
|-----|-----------------|
| `catalog://stats` | Catalog summary: counts per category, schema versions |
| `catalog://categories/{category}` | Full list of parts for a category |
| `catalog://parts/{part_id}` | Single part by ID |
| `catalog://presets` | Index of mission presets |
| `catalog://presets/{filename}` | Full body of a preset |
| `schema://parts_library` | JSON Schema for the parts library |
| `schema://mission_project` | JSON Schema for MissionProject v2 |

Categories: `airframes`, `motors`, `escs`, `batteries`,
`flight_controllers`, `radios`, `sensors`, `accessories`.

Preset filenames: `preset_long_range_relay.json`,
`preset_endurance_survey.json`, `preset_urban_congested.json`,
`preset_cold_weather.json`, `preset_tinywhoop_indoor.json`,
`preset_sub_250g.json`, `preset_beginner_5in.json`.

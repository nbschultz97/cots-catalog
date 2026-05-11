# Bring your own data pack

The bundled `data/` is a public-safe FPV reference pack. Override with
`ARCHITECT_DATA_DIR`:

```bash
export ARCHITECT_DATA_DIR=/path/to/my-catalog
architect-companion-mcp
```

Your custom catalog needs:

- `parts_library.json` conforming to the schema in
  `data/schema/parts_library_schema.json`.
- `preset_*.json` files following MissionProject v2.
- `environment_taxonomy.json` with `environmentBands`, `altitudeBands`,
  `temperatureBands`, `rfEnvironments`, and `missionTypes` lists.

Run `architect-companion-mcp --diagnostics` after pointing at your pack
to surface any validation errors before connecting an MCP client.

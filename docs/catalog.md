# Catalog categories

| Category | What it is | Required fields |
|----------|------------|------------------|
| `airframes` | Frames, RTF drones | `id`, `name`, `type`, `weight_g` |
| `motors` | Brushless motors | `id`, `name`, `kv`, `weight_g`, `max_thrust_g` |
| `escs` | Single + 4-in-1 ESCs | `id`, `name`, `max_current_a`, `weight_g` |
| `batteries` | LiPo / Li-ion / LiHV | `id`, `name`, `chemistry`, `voltage_nominal_v`, `capacity_mah`, `weight_g` |
| `flight_controllers` | Standalone + AIO FCs | `id`, `name`, `weight_g` |
| `radios` | Control / video / telemetry | `id`, `name`, `type`, `frequency_band`, `weight_g` |
| `sensors` | Cameras, VTX, goggles, GPS, IMU | `id`, `name`, `type`, `weight_g` |
| `accessories` | Props, antennas, cables | `id`, `name`, `category`, `weight_g` |

All entries also carry `data_source: {url, fetched_at, parser}` — the
URL points to a manufacturer / authoritative product page.

See `data/schema/parts_library_schema.json` for the full schema.

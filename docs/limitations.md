# Known limitations

What the compatibility engine **does** catch — see
[Compatibility rules](compatibility.md).

What it **does not** catch:

- Battery C-rating vs sustained (not peak) current draw.
- Frame battery-bay dimensions vs battery dimensions.
- Antenna polarization (RHCP vs LHCP) between TX and RX.
- VTX output power legality for the operator's regulatory region.
- Goggle ↔ VTX protocol compat (Analog ↔ Walksnail ↔ DJI ↔ HDZero).
- Actual thrust headroom or hover stability — use `estimate_thrust`.

The endurance tool is an approximation. See [Physics](physics.md) for
the model and its honest accuracy band.

## What's intentionally out of scope

- Live sync with COTS-Architect — re-vendor `data/` instead.
- Mesh routing / link-budget compute.
- Cost roll-ups beyond per-part sums.
- Regulatory / airspace / NOTAM checks.
- Flight simulation.

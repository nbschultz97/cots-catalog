# Compatibility rules

The compatibility engine runs these checks in order:

1. **Battery voltage gate** — nominal voltage falls inside ESC, FC, and
   motor voltage ranges.
2. **Weight budget** — total component weight ≤ airframe
   `max_payload_g`.
3. **Motor count** — airframe `motor_count` matches number of motor
   entries listed (or 1, treated as a spec line).
4. **ESC count** — non-integrated ESCs match `motor_count`, or a single
   4-in-1 covers them.
5. **KV vs prop size** — motor KV inside the rough band for the airframe's
   prop size class.
6. **Mount pattern** — motor / FC / airframe mount-hole patterns match
   (16×16 / 20×20 / 25.5×25.5 / 30.5×30.5).
7. **RF band overlap** — control and video radios on different bands.
8. **ESC current** — ESC `max_current_a` ≥ motor peak current.

## Known limitations

- Battery C-rating vs sustained (not peak) current draw.
- Frame battery-bay dimensions vs battery dimensions.
- Antenna polarization (RHCP vs LHCP) between TX and RX.
- VTX output power legality for the operator's region.
- Goggle ↔ VTX protocol compat (Analog ↔ Walksnail ↔ DJI ↔ HDZero).
- Thrust headroom — see [physics](physics.md).

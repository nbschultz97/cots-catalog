"""Simple hover-endurance math for sUAS configurations.

This is not a flight simulator. It applies a textbook approximation:

    endurance_min = (capacity_Ah / draw_A) * 60 * (1 - reserve_pct)

with a payload weight penalty applied as a multiplicative bump on draw.
Use it to sanity-check whether a build is in the right neighborhood, not
to publish endurance specs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .catalog import part_by_id


def _resolve_airframe(airframe_id: Optional[str], platform_weight_g: Optional[float]) -> float:
    if platform_weight_g is not None:
        return float(platform_weight_g)
    if airframe_id:
        part = part_by_id(airframe_id)
        if part is None or part["_category"] != "airframes":
            raise ValueError(f"Airframe ID '{airframe_id}' not found in catalog")
        return float(part.get("weight_g") or 0)
    raise ValueError("Must supply either airframe_id or platform_weight_g")


def _resolve_battery(
    battery_id: Optional[str],
    battery_mah: Optional[float],
    battery_v: Optional[float],
) -> Dict[str, float]:
    if battery_id:
        part = part_by_id(battery_id)
        if part is None or part["_category"] != "batteries":
            raise ValueError(f"Battery ID '{battery_id}' not found in catalog")
        return {
            "mah": float(part.get("capacity_mah") or 0),
            "v": float(part.get("voltage_nominal_v") or 0),
            "g": float(part.get("weight_g") or 0),
            "source": part.get("name", battery_id),
        }
    if battery_mah is None:
        raise ValueError("Must supply battery_id or battery_mah")
    return {
        "mah": float(battery_mah),
        "v": float(battery_v) if battery_v is not None else 0.0,
        "g": 0.0,
        "source": "raw inputs",
    }


def estimate_flight_time(
    airframe_id: Optional[str] = None,
    battery_id: Optional[str] = None,
    *,
    platform_weight_g: Optional[float] = None,
    battery_mah: Optional[float] = None,
    battery_v: Optional[float] = None,
    payload_weight_g: float = 0.0,
    avg_current_draw_a: float = 15.0,
    reserve_pct: float = 0.2,
) -> Dict[str, Any]:
    """Estimate flight time, accepting catalog IDs or raw numbers.

    The defaults mirror an average 5" cinematic multirotor: 15A average
    draw, 20% reserve. Override either via the catalog or via raw inputs.
    """

    platform_g = _resolve_airframe(airframe_id, platform_weight_g)
    battery = _resolve_battery(battery_id, battery_mah, battery_v)

    total_weight_g = platform_g + payload_weight_g + battery["g"]
    weight_factor = 1.0 + (payload_weight_g / max(platform_g, 1.0)) * 0.3
    effective_draw_a = avg_current_draw_a * weight_factor
    raw_endurance_min = (battery["mah"] / 1000.0) / max(effective_draw_a, 0.1) * 60.0
    safe_endurance_min = raw_endurance_min * (1.0 - reserve_pct)

    return {
        "airframe_id": airframe_id,
        "battery_id": battery_id,
        "battery_source": battery["source"],
        "platform_weight_g": platform_g,
        "payload_weight_g": payload_weight_g,
        "total_weight_g": round(total_weight_g, 1),
        "battery_mah": battery["mah"],
        "battery_v": battery["v"],
        "weight_factor": round(weight_factor, 3),
        "effective_current_a": round(effective_draw_a, 2),
        "raw_endurance_min": round(raw_endurance_min, 1),
        "safe_endurance_min": round(safe_endurance_min, 1),
        "reserve_pct": int(reserve_pct * 100),
        "note": (
            "Hover approximation. Forward flight typically ±15%. "
            "Not a flight simulator — sanity-check only."
        ),
    }

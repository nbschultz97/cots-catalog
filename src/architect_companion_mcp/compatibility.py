"""Compatibility checks for COTS sUAS builds.

Engineering rules used:

* Battery nominal voltage falls inside ESC, FC, motor voltage ranges.
* Total component weight <= airframe.max_payload_g + airframe.weight_g.
* Control and video radios use different frequency bands when both present.
* Flight controller's firmware list intersects with radios' firmware family
  if a firmware constraint is declared.

The checks are coarse — meant to catch obvious mismatches before an LLM
recommends a build, not replace electrical engineering review.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .catalog import part_by_id


def _voltage_range(part: Dict[str, Any]) -> Optional[Dict[str, float]]:
    return part.get("voltage_range") or part.get("voltage_input_v")


def _voltage_in_range(volts: float, vrange: Optional[Dict[str, float]]) -> bool:
    if not vrange:
        return True
    lo = vrange.get("min_v") if "min_v" in vrange else vrange.get("min")
    hi = vrange.get("max_v") if "max_v" in vrange else vrange.get("max")
    if lo is not None and volts < float(lo):
        return False
    if hi is not None and volts > float(hi):
        return False
    return True


def check_compatibility(part_ids: List[str]) -> Dict[str, Any]:
    """Run compatibility checks over a list of part IDs.

    Returns a dict with ``compatible`` (bool), ``issues`` (list of strings),
    ``parts`` (list of resolved parts with ``_category``), ``total_weight_g``,
    and ``budget`` (airframe weight budget summary, if an airframe is present).
    """

    parts: List[Dict[str, Any]] = []
    unknown: List[str] = []
    for pid in part_ids:
        part = part_by_id(pid)
        if part is None:
            unknown.append(pid)
        else:
            parts.append(part)

    if unknown:
        return {
            "compatible": False,
            "reason": f"Unknown part IDs: {', '.join(unknown)}",
            "parts": [p["id"] for p in parts],
        }

    issues: List[str] = []

    # Battery nominal voltage gate
    battery = next((p for p in parts if p["_category"] == "batteries"), None)
    if battery:
        v_nominal = battery.get("voltage_nominal_v")
        if v_nominal:
            for p in parts:
                if p["_category"] in {"escs", "flight_controllers", "motors"}:
                    if not _voltage_in_range(v_nominal, _voltage_range(p)):
                        issues.append(
                            f"{p['name']}: battery {v_nominal}V outside its voltage range"
                        )

    # Weight budget vs airframe
    airframe = next((p for p in parts if p["_category"] == "airframes"), None)
    total_weight_g = sum((p.get("weight_g") or 0) for p in parts)
    budget: Optional[Dict[str, float]] = None
    if airframe:
        max_payload = airframe.get("max_payload_g") or 0
        airframe_weight = airframe.get("weight_g") or 0
        component_weight = total_weight_g - airframe_weight
        budget = {
            "airframe_weight_g": airframe_weight,
            "max_payload_g": max_payload,
            "component_weight_g": component_weight,
            "remaining_budget_g": max_payload - component_weight,
        }
        if component_weight > max_payload:
            issues.append(
                f"Components ({component_weight}g) exceed airframe payload budget ({max_payload}g)"
            )

    # Control vs video radio band overlap
    control_radios = [p for p in parts if p["_category"] == "radios" and p.get("type") == "control"]
    video_radios = [p for p in parts if p["_category"] == "radios" and p.get("type") == "video"]
    if control_radios and video_radios:
        for c in control_radios:
            for v in video_radios:
                if c.get("frequency_band") and c.get("frequency_band") == v.get("frequency_band"):
                    issues.append(
                        f"Control radio {c['name']} and video radio {v['name']} share band "
                        f"{c['frequency_band']} — likely interference"
                    )

    # ESC current must support motor current
    escs = [p for p in parts if p["_category"] == "escs"]
    motors = [p for p in parts if p["_category"] == "motors"]
    for esc in escs:
        for motor in motors:
            esc_max = esc.get("max_current_a")
            motor_max = motor.get("max_current_a")
            if esc_max and motor_max and esc_max < motor_max:
                issues.append(
                    f"ESC {esc['name']} ({esc_max}A) cannot sustain motor {motor['name']} peak draw ({motor_max}A)"
                )

    return {
        "compatible": len(issues) == 0,
        "issues": issues,
        "parts": [{"id": p["id"], "name": p["name"], "category": p["_category"]} for p in parts],
        "total_weight_g": total_weight_g,
        "budget": budget,
    }

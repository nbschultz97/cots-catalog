"""Compatibility checks for COTS sUAS builds.

Engineering rules applied (in order):

* Battery nominal voltage falls inside ESC, FC, motor voltage ranges.
* Total component weight fits in the airframe payload budget.
* Airframe motor_count matches the number of motors listed (or 1, treated
  as a spec line). ESC count or one integrated 4-in-1 covers the motors.
* Motor KV vs prop size sanity (high-KV + big prop → burnout flag;
  low-KV + small prop → underprop flag).
* Control and video radios use different frequency bands when both present.
* ESC max current covers motor peak current.

Coarse checks meant to catch obvious mistakes before an LLM recommends a
build, not replace electrical engineering review.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .catalog import part_by_id

# Heuristic KV bands per prop size (inches). Rough rule of thumb from
# FPV builder community — tune as the catalog grows.
_KV_BANDS: List[Dict[str, Any]] = [
    {"prop_min": 4.5, "prop_max": 5.5, "kv_min": 1800, "kv_max": 2700},
    {"prop_min": 5.5, "prop_max": 7.5, "kv_min": 1100, "kv_max": 2000},
    {"prop_min": 7.5, "prop_max": 9.5, "kv_min": 900,  "kv_max": 1600},
    {"prop_min": 9.5, "prop_max": 13.0, "kv_min": 600,  "kv_max": 1200},
]


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


def _parse_prop_inches(prop_size: Optional[str]) -> Optional[float]:
    """Parse the diameter inches from strings like '5x4.3' or '7x3.5' or '10x5x3'."""
    if not prop_size:
        return None
    match = re.match(r"(\d+(?:\.\d+)?)", str(prop_size))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _kv_band(prop_inches: float) -> Optional[Dict[str, Any]]:
    for band in _KV_BANDS:
        if band["prop_min"] <= prop_inches < band["prop_max"]:
            return band
    return None


def check_compatibility(part_ids: List[str]) -> Dict[str, Any]:
    """Run compatibility checks over a list of part IDs.

    Returns ``compatible`` (bool), ``issues`` (list of strings),
    ``parts`` (resolved parts with their category), ``total_weight_g``,
    and ``budget`` (airframe weight budget summary).
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

    airframe = next((p for p in parts if p["_category"] == "airframes"), None)
    batteries = [p for p in parts if p["_category"] == "batteries"]
    motors = [p for p in parts if p["_category"] == "motors"]
    escs = [p for p in parts if p["_category"] == "escs"]
    radios = [p for p in parts if p["_category"] == "radios"]

    # Battery voltage gate
    battery = batteries[0] if batteries else None
    if battery:
        v_nominal = battery.get("voltage_nominal_v")
        if v_nominal:
            for p in parts:
                if p["_category"] in {"escs", "flight_controllers", "motors"}:
                    if not _voltage_in_range(v_nominal, _voltage_range(p)):
                        issues.append(
                            f"{p['name']}: battery {v_nominal}V outside its voltage range"
                        )

    # Weight budget vs airframe payload
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

    # Motor count vs airframe motor_count (treat 1 motor as a spec line)
    if airframe and airframe.get("motor_count"):
        expected_motors = int(airframe.get("motor_count") or 0)
        motor_count = len(motors)
        if expected_motors > 1 and motor_count not in (0, 1, expected_motors):
            issues.append(
                f"Airframe expects {expected_motors} motors; build lists {motor_count}. "
                f"List each motor or a single spec line covering the set."
            )
        # ESC count vs motors. An integrated 4-in-1 counts for all expected motors.
        if expected_motors > 1 and escs:
            integrated_4in1 = any(e.get("integrated") for e in escs)
            single_escs = [e for e in escs if not e.get("integrated")]
            if not integrated_4in1 and len(single_escs) not in (0, 1, expected_motors):
                issues.append(
                    f"Airframe expects {expected_motors} ESCs (or one {expected_motors}-in-1); "
                    f"build has {len(single_escs)} single ESC(s) and no integrated stack."
                )

    # Motor KV vs prop size sanity
    prop_inches = _parse_prop_inches(airframe.get("prop_size") if airframe else None)
    if prop_inches is not None:
        band = _kv_band(prop_inches)
        for motor in motors:
            kv = motor.get("kv")
            if kv is None or band is None:
                continue
            if kv > band["kv_max"]:
                issues.append(
                    f"Motor {motor['name']} ({kv}KV) too high for {prop_inches}\" prop "
                    f"— suggested {band['kv_min']}-{band['kv_max']}KV. Overcurrent / burnout risk."
                )
            elif kv < band["kv_min"]:
                issues.append(
                    f"Motor {motor['name']} ({kv}KV) too low for {prop_inches}\" prop "
                    f"— suggested {band['kv_min']}-{band['kv_max']}KV. Insufficient thrust."
                )

    # Control vs video radio band overlap
    control_radios = [p for p in radios if p.get("type") == "control"]
    video_radios = [p for p in radios if p.get("type") == "video"]
    if control_radios and video_radios:
        for c in control_radios:
            for v in video_radios:
                if c.get("frequency_band") and c.get("frequency_band") == v.get("frequency_band"):
                    issues.append(
                        f"Control radio {c['name']} and video radio {v['name']} share band "
                        f"{c['frequency_band']} — likely interference"
                    )

    # ESC current must support motor current
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

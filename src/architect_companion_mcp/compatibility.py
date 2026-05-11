"""Compatibility checks for COTS sUAS builds.

Engineering rules applied (in order):

* Battery nominal voltage falls inside ESC, FC, motor voltage ranges.
* Total component weight fits in the airframe payload budget.
* Airframe motor_count matches the number of motors listed (or 1, treated
  as a spec line). ESC count or one integrated 4-in-1 covers the motors.
* Motor KV vs prop size sanity (high-KV + big prop → burnout flag;
  low-KV + small prop → underprop flag).
* Motor mount pattern matches airframe motor mount pattern.
* Flight controller mounting pattern matches a known FC mount slot.
* Control and video radios use different frequency bands when both present.
* ESC max current covers motor peak current.

Coarse checks meant to catch obvious mistakes before an LLM recommends a
build, not replace electrical engineering review.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .catalog import part_by_id

# Canonical FC / ESC mount patterns (mm). Used as a set of "known good"
# patterns when a motor lists e.g. "16x16" — the engine pairs it against
# any FC also at 16x16.
_KNOWN_FC_MOUNTS = {"20x20", "25.5x25.5", "30.5x30.5", "16x16"}


def _normalize_mount(value: Any) -> Optional[str]:
    """Pull "16x16" / "30.5x30.5" out of various string formats."""
    if not value:
        return None
    text = str(value).lower().replace("mm", "").replace(" ", "")
    match = re.search(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", text)
    if match:
        a, b = match.group(1), match.group(2)
        try:
            af = float(a)
            bf = float(b)
        except ValueError:
            return None
        return f"{af:g}x{bf:g}"
    return None

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

    # Mount pattern: motor mount vs airframe mount; FC mount vs FC stack
    flight_controllers = [p for p in parts if p["_category"] == "flight_controllers"]
    if airframe:
        airframe_mount = _normalize_mount(
            airframe.get("motor_mount") or airframe.get("motor_mount_mm")
        )
        for motor in motors:
            motor_mount = _normalize_mount(motor.get("mount_pattern") or motor.get("mount"))
            if airframe_mount and motor_mount and airframe_mount != motor_mount:
                issues.append(
                    f"Motor {motor['name']} mount {motor_mount} does not match "
                    f"airframe mount {airframe_mount}."
                )
    for fc in flight_controllers:
        fc_mount = _normalize_mount(fc.get("mounting") or fc.get("mount_pattern"))
        if fc_mount and fc_mount not in _KNOWN_FC_MOUNTS:
            issues.append(
                f"FC {fc['name']} mount {fc_mount} is not a standard FC stack "
                f"({', '.join(sorted(_KNOWN_FC_MOUNTS))})."
            )

    # Goggle / VTX protocol matrix. Walksnail, DJI, HDZero, and Analog
    # are all incompatible with each other — if the build has parts from
    # two different ecosystems, flag it. Read protocol from tags.
    sensors = [p for p in parts if p["_category"] == "sensors"]

    def _protocol_of(part: Dict[str, Any]) -> Optional[str]:
        tag_protocols = {"walksnail", "dji", "hdzero", "hdz"}
        tags = {(t or "").lower() for t in (part.get("tags") or [])}
        for tp in tag_protocols:
            if tp in tags:
                return tp.replace("hdz", "hdzero")
        # Analog as fallback if interface mentions NTSC/PAL/Analog
        interface = (part.get("interface") or "").lower()
        if "analog" in interface or "ntsc" in interface or "pal" in interface:
            return "analog"
        if "digital" in interface and not tags & tag_protocols:
            return "digital-unknown"
        return None

    sensor_protocols = {_protocol_of(s) for s in sensors if _protocol_of(s)}
    sensor_protocols.discard(None)
    sensor_protocols.discard("digital-unknown")
    if len(sensor_protocols) > 1:
        issues.append(
            f"Mixed video ecosystem detected: {', '.join(sorted(sensor_protocols))}. "
            f"VTXes and goggles must share one protocol (analog / walksnail / DJI / HDZero)."
        )

    # Antenna polarization sanity: if any antenna accessory is in the
    # build, its polarization tag (rhcp / lhcp) should appear on the
    # paired VTX accessory or radio. Otherwise flag a likely mismatch.
    accessories = [p for p in parts if p["_category"] == "accessories"]
    antennas = [a for a in accessories if "antenna" in (a.get("category") or "").lower()
                or any("antenna" in (t or "").lower() for t in (a.get("tags") or []))]
    pol_tags = {"rhcp", "lhcp"}
    if antennas:
        antenna_pols = set()
        for a in antennas:
            for tag in (a.get("tags") or []):
                if tag.lower() in pol_tags:
                    antenna_pols.add(tag.lower())
        if len(antenna_pols) > 1:
            issues.append(
                f"Mixed antenna polarizations: {sorted(antenna_pols)}. "
                f"TX and RX antennas should share polarization (both RHCP or both LHCP)."
            )

    # Battery C-rating vs sustained current. Sustained current ≈ peak ÷ 2
    # for typical FPV builds. If battery max_discharge_a (= C × Ah)
    # can't cover the per-motor peak × motor_count × 0.5, flag.
    if battery and motors and airframe:
        max_discharge_a = battery.get("max_discharge_a")
        if not max_discharge_a:
            c_rating = battery.get("c_rating")
            capacity_mah = battery.get("capacity_mah")
            if c_rating and capacity_mah:
                max_discharge_a = float(c_rating) * float(capacity_mah) / 1000.0
        if max_discharge_a:
            n_motors_expected = int(airframe.get("motor_count") or len(motors) or 1)
            peak_per_motor = max((m.get("max_current_a") or 0) for m in motors)
            sustained_estimate_a = peak_per_motor * n_motors_expected * 0.5
            if sustained_estimate_a > max_discharge_a:
                issues.append(
                    f"Battery sustained discharge ({max_discharge_a:.0f}A) likely "
                    f"insufficient for build (estimated ~{sustained_estimate_a:.0f}A "
                    f"sustained = {peak_per_motor:.0f}A peak × {n_motors_expected} motors × 0.5)."
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

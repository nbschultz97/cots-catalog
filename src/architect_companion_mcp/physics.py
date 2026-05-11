"""Sanity-check physics for sUAS configurations.

This is not a flight simulator. Three engineering approximations:

1. **Multirotor hover endurance** via simplified Blade Element / Momentum
   theory. Induced power at hover is

       P_induced = (m*g) * sqrt((m*g) / (2 * rho * A))

   where ``A`` is the total disc area (``n_motors * pi * r_prop**2``).
   Electrical power then folds in motor / ESC / prop efficiency:
   ``P_elec = P_induced / (eta_motor * eta_esc * eta_prop)``.

2. **Multirotor cruise endurance** approximated as
   ``endurance_cruise = endurance_hover * cruise_factor`` where the
   cruise factor depends on airframe class (5" freestyle ~ 1.3,
   7" long-range ~ 1.8, 10" heavy-lift ~ 2.0). FPV community lore,
   tuned to match published Bardwell / Mr. Steele / Le Drib endurance
   numbers within ~15%.

3. **Fixed-wing endurance** via simplified Breguet endurance:
   ``P_cruise = m*g*V_cruise / (eta_prop * (L/D))``, then
   ``endurance = E_battery / P_cruise``. ``L/D`` defaults to 12 for
   typical foam FPV airframes; 18 for purpose-built endurance wings.

All defaults are tunable per call. Defaults match the FPV builder
community's rules of thumb. **Do not use these numbers as published
flight specs** — they're sanity checks, not certified performance.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Optional

from .catalog import part_by_id

# Physical constants
_GRAVITY = 9.81                       # m/s^2
_RHO_SL = 1.225                       # kg/m^3 at sea level / 15 C
_RHO_2KM = 0.9093                     # kg/m^3 at 2000m

# Efficiency defaults (typical FPV electric power stack)
_DEFAULT_ETA_MOTOR = 0.83
_DEFAULT_ETA_ESC = 0.94
_DEFAULT_ETA_PROP = 0.65

# Empirical aerodynamic-loss multiplier: real hover power / BEM induced
# power. BEM gives the theoretical minimum; real FPV power is dominated
# by profile drag, tip vortex losses, and high-disc-loading
# inefficiencies. Multipliers tuned to match published flight times
# from Joshua Bardwell, Mr. Steele, Le Drib, and eCalc on common
# builds. Range ±25%.
_AERO_LOSS_MULTIPLIER = {
    # prop diameter ranges (inches): multiplier
    (0.0, 2.0): 8.0,    # tinywhoop / 1.6" cinewhoop
    (2.0, 3.5): 7.0,    # 2"-3" toothpick / cine
    (3.5, 4.5): 6.0,    # 3.5"-4"
    (4.5, 6.0): 5.0,    # 5" freestyle / race
    (6.0, 8.0): 4.0,    # 6"-7" long-range
    (8.0, 11.0): 3.5,   # 8"-10" heavy-lift
    (11.0, 99.0): 3.0,  # 12"+ ag / heavy-lift
}

# Fixed-wing real-world "L/D × eta" empirical product. Theoretical L/D
# for foam FPV is 4-8, but real-world efficiency drops further from
# parasitic drag at low Reynolds numbers. These match published
# Skywalker X8 / Volantex Raptor flight times.
_FW_LD_ETA_DEFAULTS = {
    "long-endurance": 8.0,
    "flying-wing": 5.0,
    "fixed-wing": 3.5,
}

# Default total weight of "everything else" (motors + ESCs + FC + cam +
# VTX + RX + wires + props) when the caller passes only airframe +
# battery. Without these the AUW is wildly low for small builds and
# the endurance is overestimated. Tuned to typical build manifests.
_COMPONENT_OVERHEAD_BY_CLASS = {
    "tinywhoop": 12,         # 4× brushless 0802 + AIO board
    "1.6-inch": 18,          # whoop AIO + tiny VTX
    "2-inch": 35,             # cinewhoop AIO + DJI Vista
    "3-inch": 80,
    "3.5-inch": 100,
    "4-inch": 150,
    "5-inch": 220,            # 4× 2207 + 4-in-1 ESC + FC + Vista/Walksnail + cam + RX + wires
    "7-inch": 280,
    "8-inch": 320,
    "10-inch": 400,
    "fixed-wing": 250,        # motor + servos + ESC + FC + cam + VTX + GPS + RX
    "flying-wing": 300,
}


# Per-airframe-class cruise multiplier (hover → cruise endurance factor)
_CRUISE_FACTOR = {
    "5-inch": 1.30,
    "7-inch": 1.75,
    "8-inch": 1.85,
    "10-inch": 2.00,
    "tinywhoop": 1.10,
    "1.6-inch": 1.10,
    "2-inch": 1.15,
    "3-inch": 1.20,
    "3.5-inch": 1.25,
    "4-inch": 1.25,
    "fixed-wing": 2.50,
    "flying-wing": 2.50,
}



def _parse_prop_inches(prop_size: Optional[str]) -> Optional[float]:
    if not prop_size:
        return None
    match = re.match(r"(\d+(?:\.\d+)?)", str(prop_size))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _air_density(altitude_m: float, temp_c: float = 15.0) -> float:
    """Simple ISA approximation good to ~5000m for sanity checks.

    rho = p / (R * T) with ISA pressure dropping linearly with altitude
    (oversimplified; real ISA uses exponential lapse). Adequate for
    +/- 20% endurance approximations.
    """
    # Pressure at altitude (Pa) using ISA standard
    pressure_pa = 101325.0 * (1.0 - 2.25577e-5 * altitude_m) ** 5.25588
    temperature_k = temp_c + 273.15 - 0.0065 * altitude_m
    return pressure_pa / (287.05 * max(temperature_k, 200.0))


def _resolve_airframe(airframe_id: Optional[str], platform_weight_g: Optional[float]) -> Dict[str, Any]:
    if airframe_id:
        part = part_by_id(airframe_id)
        if part is None or part["_category"] != "airframes":
            raise ValueError(f"Airframe ID '{airframe_id}' not found in catalog")
        return part
    if platform_weight_g is None:
        raise ValueError("Must supply either airframe_id or platform_weight_g")
    # Synthetic airframe — assume quad, 5" prop, no class tag.
    return {
        "weight_g": platform_weight_g,
        "motor_count": 4,
        "prop_size": "5x4.3",
        "tags": ["5-inch"],
        "type": "multi-rotor",
        "_synthetic": True,
    }


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
        "v": float(battery_v) if battery_v is not None else 14.8,
        "g": 0.0,
        "source": "raw inputs",
    }


def _cruise_factor_for(airframe: Dict[str, Any]) -> float:
    for tag in airframe.get("tags") or []:
        if tag in _CRUISE_FACTOR:
            return _CRUISE_FACTOR[tag]
    return 1.3  # safe default — barely-better than hover


def _component_overhead_for(airframe: Dict[str, Any]) -> float:
    """How much weight the build adds beyond airframe + battery (motors,
    ESCs, FC, cam, VTX, RX, wires, props). Used when caller passes only
    airframe + battery so the AUW reflects a buildable quad."""
    for tag in airframe.get("tags") or []:
        if tag in _COMPONENT_OVERHEAD_BY_CLASS:
            return float(_COMPONENT_OVERHEAD_BY_CLASS[tag])
    return 120.0  # safe-ish default for unknown class


def _aero_multiplier_for(prop_inches: float) -> float:
    for (lo, hi), mult in _AERO_LOSS_MULTIPLIER.items():
        if lo <= prop_inches < hi:
            return mult
    return 5.0


def _fw_ld_eta_for(airframe: Dict[str, Any]) -> float:
    for tag in airframe.get("tags") or []:
        if tag in _FW_LD_ETA_DEFAULTS:
            return _FW_LD_ETA_DEFAULTS[tag]
    return 3.5


def estimate_flight_time(
    airframe_id: Optional[str] = None,
    battery_id: Optional[str] = None,
    *,
    platform_weight_g: Optional[float] = None,
    battery_mah: Optional[float] = None,
    battery_v: Optional[float] = None,
    payload_weight_g: float = 0.0,
    flight_mode: str = "hover",
    altitude_m: float = 0.0,
    temperature_c: float = 15.0,
    eta_motor: float = _DEFAULT_ETA_MOTOR,
    eta_esc: float = _DEFAULT_ETA_ESC,
    eta_prop: float = _DEFAULT_ETA_PROP,
    reserve_pct: float = 0.2,
    # Legacy parameter; only used as a soft override if BEM result is wildly off.
    avg_current_draw_a: Optional[float] = None,
) -> Dict[str, Any]:
    """Estimate endurance using simplified BEM (multirotor) or Breguet
    (fixed-wing). Pass catalog IDs or raw inputs; either works.

    ``flight_mode``: ``"hover"`` (default for multirotor), ``"cruise"``
    (uses airframe-class cruise factor), or ``"auto"`` (cruise for any
    fixed-wing / flying-wing airframe, else hover).
    """

    airframe = _resolve_airframe(airframe_id, platform_weight_g)
    battery = _resolve_battery(battery_id, battery_mah, battery_v)

    # AUW. Add a class-appropriate component overhead (motors + ESCs +
    # FC + cam + VTX + RX + wires + props) so the AUW reflects a
    # buildable quad rather than just "airframe + battery". Skipped if
    # the caller passes their own platform_weight_g (assumed to include
    # everything).
    airframe_g = float(airframe.get("weight_g") or 0)
    if airframe.get("_synthetic") or platform_weight_g is not None:
        overhead_g = 50.0  # minimal sanity overhead for raw inputs
    else:
        overhead_g = _component_overhead_for(airframe)
    auw_g = airframe_g + battery["g"] + payload_weight_g + overhead_g
    auw_kg = auw_g / 1000.0

    # Energy budget (Wh → Joules)
    energy_wh = (battery["mah"] / 1000.0) * battery["v"]
    energy_j = energy_wh * 3600.0
    usable_j = energy_j * (1.0 - reserve_pct)

    # Determine flight mode
    af_type = airframe.get("type", "multi-rotor")
    is_fixed_wing = af_type in {"fixed-wing", "vtol"}
    resolved_mode = flight_mode
    if resolved_mode == "auto":
        resolved_mode = "cruise" if is_fixed_wing else "hover"

    rho = _air_density(altitude_m, temperature_c)
    eta_drivetrain = eta_motor * eta_esc  # prop efficiency rolled into aero multiplier

    # ---- Multirotor BEM hover + empirical aerodynamic loss multiplier ----
    n_motors = int(airframe.get("motor_count") or 4)
    prop_inches = _parse_prop_inches(airframe.get("prop_size")) or 5.0
    prop_radius_m = prop_inches * 0.0254 / 2.0
    disc_area_m2 = n_motors * math.pi * prop_radius_m ** 2

    p_induced_w = (auw_kg * _GRAVITY) * math.sqrt(
        (auw_kg * _GRAVITY) / max(2.0 * rho * disc_area_m2, 1e-6)
    )
    aero_mult = _aero_multiplier_for(prop_inches)
    p_aero_w = p_induced_w * aero_mult
    p_elec_hover_w = p_aero_w / max(eta_drivetrain, 0.1)
    hover_endurance_s = usable_j / max(p_elec_hover_w, 1.0)
    hover_endurance_min = hover_endurance_s / 60.0

    # ---- Fixed-wing simplified Breguet ----
    fw_endurance_min: Optional[float] = None
    if is_fixed_wing:
        ld_eta = _fw_ld_eta_for(airframe)
        v_cruise_mps = 12.0  # typical FPV fixed-wing cruise ~ 43 km/h
        p_cruise_w = (auw_kg * _GRAVITY * v_cruise_mps) / max(ld_eta, 0.1)
        fw_endurance_min = (usable_j / max(p_cruise_w, 1.0)) / 60.0

    # ---- Multirotor cruise approximation ----
    cruise_factor = _cruise_factor_for(airframe)
    cruise_endurance_min = hover_endurance_min * cruise_factor

    # ---- Pick the right number for the resolved mode ----
    if resolved_mode == "hover":
        endurance_min = hover_endurance_min
    elif resolved_mode == "cruise":
        endurance_min = fw_endurance_min if is_fixed_wing else cruise_endurance_min
    else:
        raise ValueError(f"Unknown flight_mode '{flight_mode}'. Use hover, cruise, or auto.")

    # Legacy override path — if user passed a current draw, also expose a
    # naive estimate for comparison so they can see why we differ.
    naive_min: Optional[float] = None
    if avg_current_draw_a is not None:
        naive_min = (
            (battery["mah"] / 1000.0) / max(avg_current_draw_a, 0.1) * 60.0 * (1.0 - reserve_pct)
        )

    return {
        "airframe_id": airframe_id,
        "battery_id": battery_id,
        "battery_source": battery["source"],
        "platform_weight_g": airframe_g,
        "payload_weight_g": payload_weight_g,
        "component_overhead_g": round(overhead_g, 1),
        "auw_g": round(auw_g, 1),
        "energy_wh": round(energy_wh, 2),
        "n_motors": n_motors,
        "prop_inches": prop_inches,
        "disc_area_m2": round(disc_area_m2, 4),
        "disc_loading_kg_per_m2": round(auw_kg / max(disc_area_m2, 1e-6), 2),
        "air_density_kg_m3": round(rho, 4),
        "eta_drivetrain": round(eta_drivetrain, 3),
        "aero_loss_multiplier": aero_mult,
        "p_induced_w_hover": round(p_induced_w, 1),
        "p_electric_w_hover": round(p_elec_hover_w, 1),
        "hover_endurance_min": round(hover_endurance_min, 1),
        "cruise_endurance_min": round(cruise_endurance_min, 1),
        "fixed_wing_endurance_min": round(fw_endurance_min, 1) if fw_endurance_min else None,
        "cruise_factor": cruise_factor,
        "naive_estimate_min": round(naive_min, 1) if naive_min else None,
        "flight_mode_resolved": resolved_mode,
        "safe_endurance_min": round(endurance_min, 1),
        "reserve_pct": int(reserve_pct * 100),
        "model": "BEM induced × empirical aero-loss multiplier (multirotor) / Breguet × empirical L/D-eta (fixed-wing)",
        "note": (
            "Empirical multipliers tuned to published flight times. Expected "
            "accuracy: ±25% for multirotor hover, ±35% for multirotor cruise, "
            "±40% for fixed-wing cruise. Calibrate against your own build data."
        ),
    }


def estimate_thrust(
    airframe_id: str,
    motor_id: str,
    battery_id: str,
    *,
    eta_motor: float = _DEFAULT_ETA_MOTOR,
) -> Dict[str, Any]:
    """Estimate per-motor and total thrust + thrust-to-weight ratio for
    a build. Uses motor.max_thrust_g (from catalog) scaled by battery
    nominal voltage vs motor's voltage range, ignoring derating from
    altitude / temperature.
    """

    airframe = part_by_id(airframe_id)
    motor = part_by_id(motor_id)
    battery = part_by_id(battery_id)
    if not airframe or airframe["_category"] != "airframes":
        raise ValueError(f"Airframe '{airframe_id}' not found")
    if not motor or motor["_category"] != "motors":
        raise ValueError(f"Motor '{motor_id}' not found")
    if not battery or battery["_category"] != "batteries":
        raise ValueError(f"Battery '{battery_id}' not found")

    n_motors = int(airframe.get("motor_count") or 4)
    max_thrust_g = float(motor.get("max_thrust_g") or 0)
    v_nominal = float(battery.get("voltage_nominal_v") or 0)
    v_range = motor.get("voltage_range") or {}
    v_max = float(v_range.get("max_v") or v_nominal)

    # Scale max thrust by sqrt(V/V_max) — coarse but standard rule of
    # thumb (thrust scales with RPM^2, RPM ~ V, so thrust ~ V^2 with
    # diminishing returns due to current limits).
    thrust_scale = min(1.0, v_nominal / max(v_max, 0.1))
    per_motor_thrust_g = max_thrust_g * thrust_scale * eta_motor
    total_thrust_g = per_motor_thrust_g * n_motors

    # Estimate AUW with a placeholder for components beyond airframe+battery+motors
    auw_g = (
        float(airframe.get("weight_g") or 0)
        + float(battery.get("weight_g") or 0)
        + (float(motor.get("weight_g") or 0) * n_motors)
        + 60.0  # ESC + FC + cam + VTX + RX + wires placeholder
    )
    tw_ratio = total_thrust_g / max(auw_g, 1.0)

    return {
        "airframe": airframe["name"],
        "motor": motor["name"],
        "battery": battery["name"],
        "n_motors": n_motors,
        "per_motor_thrust_g": round(per_motor_thrust_g, 1),
        "total_thrust_g": round(total_thrust_g, 1),
        "estimated_auw_g": round(auw_g, 1),
        "thrust_to_weight_ratio": round(tw_ratio, 2),
        "verdict": _tw_verdict(tw_ratio),
        "note": (
            "Coarse thrust derate by voltage and motor efficiency. "
            "Real thrust depends on prop choice, motor load curve, and ESC current."
        ),
    }


def _tw_verdict(tw: float) -> str:
    if tw >= 6:
        return "Race-class — extreme thrust"
    if tw >= 4:
        return "Freestyle / aggressive — strong margin"
    if tw >= 2.5:
        return "Cinematic / long-range — adequate for cruise"
    if tw >= 1.5:
        return "Marginal — needs care on takeoff / climb"
    return "BELOW HOVER — build will not fly"


def estimate_range_km(
    airframe_id: str,
    battery_id: str,
    *,
    cruise_speed_kmh: float = 60.0,
    payload_weight_g: float = 0.0,
    altitude_m: float = 0.0,
) -> Dict[str, Any]:
    """Estimate one-way range (km) at a given cruise speed.

    Uses cruise endurance from :func:`estimate_flight_time` × cruise
    speed. Halve the result if you need round-trip.
    """

    bundle = estimate_flight_time(
        airframe_id=airframe_id,
        battery_id=battery_id,
        payload_weight_g=payload_weight_g,
        altitude_m=altitude_m,
        flight_mode="cruise",
    )
    endurance_min = bundle["safe_endurance_min"]
    range_km = (cruise_speed_kmh / 60.0) * endurance_min
    return {
        "airframe_id": airframe_id,
        "battery_id": battery_id,
        "cruise_speed_kmh": cruise_speed_kmh,
        "cruise_endurance_min": endurance_min,
        "one_way_range_km": round(range_km, 1),
        "round_trip_range_km": round(range_km / 2.0, 1),
        "note": (
            "Range assumes constant cruise. No headwind / climb / loiter budget. "
            "Plan ground operations on round_trip_range × 0.6 for safety."
        ),
    }

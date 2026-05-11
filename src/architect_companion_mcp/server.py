"""MCP server entrypoint — Architect Companion for COTS robotics."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover — offline test fallback
    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, _name: str) -> None:
            self._tools: List = []

        def tool(self):
            def decorator(func):
                self._tools.append(func)
                return func
            return decorator

        def run(self, transport: str = "stdio") -> None:
            raise RuntimeError(f"mcp package missing; cannot run transport={transport}")

from . import __version__
from .blueprints import (
    generate_mission_blueprint as _generate_blueprint,
    list_operation_types,
    list_presets,
)
from .catalog import (
    catalog_stats,
    data_dir,
    list_components as _list_components,
    part_by_id,
)
from .compatibility import check_compatibility as _check_compatibility
from .physics import (
    estimate_flight_time as _estimate_flight_time,
    estimate_thrust as _estimate_thrust,
    estimate_range_km as _estimate_range_km,
)
from .prompts import (
    compare_builds as _prompt_compare_builds,
    design_build as _prompt_design_build,
    endurance_what_if as _prompt_endurance_what_if,
    troubleshoot_build as _prompt_troubleshoot_build,
    upgrade_path as _prompt_upgrade_path,
)
from .flight_data import (
    list_flight_records as _list_flight_records,
    submit_flight_record as _submit_flight_record,
    validate_endurance_model as _validate_endurance_model,
)
from .recommend import recommend_configuration as _recommend_configuration
from .templates import (
    get_build_template as _get_build_template,
    list_build_templates as _list_build_templates,
)
from .wizard import (
    build_wizard as _build_wizard,
    suggest_alternatives as _suggest_alternatives,
)
from .resources import (
    category_resource,
    part_resource,
    preset_index_resource,
    preset_resource,
    schema_resource,
    stats_resource,
)
from .storage import EventStore

mcp = FastMCP("architect-companion-mcp")
store = EventStore(Path(os.environ.get("ARCHITECT_COMPANION_DATA_DIR", "./runtime_data")))


@mcp.tool()
def health() -> Dict[str, Any]:
    """Server health, schema versions, and catalog stats."""
    stats = catalog_stats()
    return {
        "status": "ok",
        "mode": "offline-first",
        "profile": "ceradon-cots-architect",
        "version": __version__,
        "data_dir": str(data_dir()),
        "catalog": stats,
        "operation_types": list_operation_types(),
        "presets": list_presets(),
    }


@mcp.tool()
def list_components(
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    tag: Optional[str] = None,
    availability: Optional[str] = None,
    max_weight_g: Optional[float] = None,
    max_cost_usd: Optional[float] = None,
    frequency_band: Optional[str] = None,
    limit: Optional[int] = 50,
) -> List[Dict[str, Any]]:
    """Browse the COTS parts library.

    Categories: airframes, motors, escs, batteries, flight_controllers,
    radios, sensors, accessories. All filters are AND-combined. ``limit``
    defaults to 50 to keep MCP responses small.
    """
    return _list_components(
        category=category,
        manufacturer=manufacturer,
        tag=tag,
        availability=availability,
        max_weight_g=max_weight_g,
        max_cost_usd=max_cost_usd,
        frequency_band=frequency_band,
        limit=limit,
    )


@mcp.tool()
def get_part(part_id: str) -> Dict[str, Any]:
    """Fetch a single part by its catalog ID (across all categories)."""
    part = part_by_id(part_id)
    if part is None:
        raise KeyError(f"Part '{part_id}' not found in catalog")
    return part


@mcp.tool()
def check_compatibility(part_ids: List[str]) -> Dict[str, Any]:
    """Run engineering checks (voltage chain, weight budget, RF bands, ESC
    current vs motor draw) over a list of catalog part IDs."""
    return _check_compatibility(part_ids)


@mcp.tool()
def generate_mission_blueprint(
    operation_type: str = "long_range",
    duration_hours: float = 24.0,
    environment_id: Optional[str] = None,
    team_size: int = 4,
) -> Dict[str, Any]:
    """Generate a MissionProject v2 stub for a given operation type.

    ``operation_type``: long_range, long_range_relay, relay, endurance,
    endurance_survey, survey, mapping, urban, urban_congested, race,
    racing, cold_weather, winter. Unknown types fall back to
    long_range_relay.

    ``environment_id`` is one of the environmentBands values
    (indoor, dense_urban, urban, suburban, rural, open).
    """
    return _generate_blueprint(
        operation_type=operation_type,
        duration_hours=duration_hours,
        environment_id=environment_id,
        team_size=team_size,
    )


@mcp.tool()
def estimate_flight_time(
    airframe_id: Optional[str] = None,
    battery_id: Optional[str] = None,
    platform_weight_g: Optional[float] = None,
    battery_mah: Optional[float] = None,
    battery_v: Optional[float] = None,
    payload_weight_g: float = 0.0,
    avg_current_draw_a: float = 15.0,
    reserve_pct: float = 0.2,
) -> Dict[str, Any]:
    """Estimate hover endurance for a build. Pass catalog IDs OR raw
    numbers. Not a flight simulator — sanity check only."""
    return _estimate_flight_time(
        airframe_id=airframe_id,
        battery_id=battery_id,
        platform_weight_g=platform_weight_g,
        battery_mah=battery_mah,
        battery_v=battery_v,
        payload_weight_g=payload_weight_g,
        avg_current_draw_a=avg_current_draw_a,
        reserve_pct=reserve_pct,
    )


@mcp.tool()
def recommend_configuration(
    compute_tier: str = "pi5",
    mission_type: str = "long_range",
    budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Pick a candidate kit (airframe, motor, ESC, battery, FC, radio) for
    a compute tier and mission type.

    Compute tiers: pi-zero, pi4, pi5, jetson-nano, jetson-orin-nano, x86.
    Mission types: long_range, endurance_survey, freestyle, racing,
    cinematic, cold_weather. Unknown mission types fall back to
    long_range.
    """
    return _recommend_configuration(
        compute_tier=compute_tier,
        mission_type=mission_type,
        budget_usd=budget_usd,
    )


@mcp.tool()
def record_observation(stream: str, payload: Dict[str, Any]) -> Dict[str, str]:
    """Persist a telemetry observation to local JSONL storage."""
    path = store.append(stream=stream, payload=payload)
    return {"status": "stored", "path": str(path)}


@mcp.tool()
def validate_catalog() -> Dict[str, Any]:
    """Run JSON Schema + uniqueness + required-field validation on the
    currently loaded parts library. Useful when running a custom data pack
    via ``ARCHITECT_DATA_DIR``."""
    from .validation import full_validation_report
    from .catalog import load_parts_library

    return full_validation_report(load_parts_library())


@mcp.tool()
def list_build_templates(
    mission_type: Optional[str] = None,
    airframe_class: Optional[str] = None,
    skill_level: Optional[str] = None,
    max_budget_usd: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Browse curated canonical build templates. Each template is a
    complete kit (airframe + motor + ESC + battery + FC + radio + VTX)
    with mission, skill level, and budget estimate. Filters all
    AND-combined."""
    return _list_build_templates(
        mission_type=mission_type,
        airframe_class=airframe_class,
        skill_level=skill_level,
        max_budget_usd=max_budget_usd,
    )


@mcp.tool()
def get_build_template(template_id: str) -> Dict[str, Any]:
    """Fetch a complete build template by ID, including all part slots,
    description, and notes."""
    return _get_build_template(template_id)


@mcp.tool()
def build_wizard(
    mission_type: Optional[str] = None,
    airframe_class: Optional[str] = None,
    skill_level: Optional[str] = None,
    budget_usd: Optional[float] = None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """One-shot canonical-build picker. Filters templates by mission /
    class / skill / budget, runs check_compatibility on each, and
    returns the top N with validation status attached. Compatible-first,
    then closest to budget."""
    return _build_wizard(
        mission_type=mission_type,
        airframe_class=airframe_class,
        skill_level=skill_level,
        budget_usd=budget_usd,
        top_n=top_n,
    )


@mcp.tool()
def suggest_alternatives(
    failing_part_ids: List[str],
    issue: str,
    top_n: int = 3,
) -> Dict[str, Any]:
    """When a build fails compatibility, return up to N candidate swap
    parts in the category the issue points at. Ranked by in-stock first,
    then cheapest. Run check_compatibility again after swapping."""
    return _suggest_alternatives(
        failing_part_ids=failing_part_ids,
        issue=issue,
        top_n=top_n,
    )


@mcp.tool()
def estimate_thrust(
    airframe_id: str,
    motor_id: str,
    battery_id: str,
) -> Dict[str, Any]:
    """Estimate per-motor and total thrust + thrust-to-weight ratio for a build.
    Uses motor.max_thrust_g scaled by battery voltage vs motor's voltage range.
    Returns a verdict (race-class / freestyle / cruise / marginal / below-hover)."""
    return _estimate_thrust(airframe_id, motor_id, battery_id)


@mcp.tool()
def validate_endurance_model(include_submissions: bool = True) -> Dict[str, Any]:
    """Run the endurance physics model against every record in
    ``data/flight_data.jsonl`` (and optional user submissions). Returns
    per-class MAE / MAPE plus the worst 5 predictions. Use this to
    calibrate the model against real flight data — the open-data moat
    vs closed tools."""
    return _validate_endurance_model(include_submissions=include_submissions)


@mcp.tool()
def submit_flight_record(
    label: str,
    observed_endurance_min: float,
    build: Optional[List[str]] = None,
    platform_weight_g: Optional[float] = None,
    battery_mah: Optional[float] = None,
    battery_v: Optional[float] = None,
    payload_weight_g: float = 0,
    flight_mode: str = "cruise",
    airframe_class: str = "unknown",
    source: str = "user_submission",
    notes: str = "",
) -> Dict[str, Any]:
    """Append a real flight-data record to the runtime submissions file.
    Provide either a catalog `build` list or raw `platform_weight_g +
    battery_mah`. Submissions improve the model's calibration over time."""
    return _submit_flight_record(
        label=label,
        observed_endurance_min=observed_endurance_min,
        build=build,
        platform_weight_g=platform_weight_g,
        battery_mah=battery_mah,
        battery_v=battery_v,
        payload_weight_g=payload_weight_g,
        flight_mode=flight_mode,
        airframe_class=airframe_class,
        source=source,
        notes=notes,
    )


@mcp.tool()
def list_flight_records(
    airframe_class: Optional[str] = None,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Browse flight-data records, optionally filtered by airframe class
    (5-inch, 7-inch, fixed-wing, etc.)."""
    return _list_flight_records(airframe_class=airframe_class, limit=limit)


@mcp.tool()
def estimate_range_km(
    airframe_id: str,
    battery_id: str,
    cruise_speed_kmh: float = 60.0,
    payload_weight_g: float = 0.0,
    altitude_m: float = 0.0,
) -> Dict[str, Any]:
    """Estimate one-way / round-trip range (km) at a given cruise speed.
    Uses cruise endurance × cruise speed. Plan operations on round_trip × 0.6."""
    return _estimate_range_km(
        airframe_id=airframe_id,
        battery_id=battery_id,
        cruise_speed_kmh=cruise_speed_kmh,
        payload_weight_g=payload_weight_g,
        altitude_m=altitude_m,
    )


# ---- MCP Resources (read-only catalog URIs the LLM can browse) ----

@mcp.resource("catalog://stats")
def _resource_stats() -> str:
    """Catalog summary: counts per category, schema versions."""
    return stats_resource()


@mcp.resource("catalog://categories/{category}")
def _resource_category(category: str) -> str:
    """All parts in a category. category ∈ {airframes, motors, escs,
    batteries, flight_controllers, radios, sensors, accessories}."""
    return category_resource(category)


@mcp.resource("catalog://parts/{part_id}")
def _resource_part(part_id: str) -> str:
    """A single part by its catalog ID (across all categories)."""
    return part_resource(part_id)


@mcp.resource("catalog://presets")
def _resource_preset_index() -> str:
    """Index of available mission presets."""
    return preset_index_resource()


@mcp.resource("catalog://presets/{filename}")
def _resource_preset(filename: str) -> str:
    """A single mission preset (MissionProject v2 stub)."""
    return preset_resource(filename)


@mcp.resource("schema://parts_library")
def _resource_schema_parts() -> str:
    """JSON Schema for parts_library.json (v1.1.0)."""
    return schema_resource("parts_library")


@mcp.resource("schema://mission_project")
def _resource_schema_mission() -> str:
    """JSON Schema for MissionProject v2 documents."""
    return schema_resource("mission_project")


# ---- MCP Prompts (templated workflows) ----

@mcp.prompt()
def design_build(
    mission: str = "freestyle",
    budget_usd: float | None = None,
    compute_tier: str = "pi5",
    skill: str = "intermediate",
) -> str:
    """Templated build-design workflow: recommend → validate → swap → report."""
    return _prompt_design_build(mission, budget_usd, compute_tier, skill)


@mcp.prompt()
def compare_builds(build_a_ids: str, build_b_ids: str) -> str:
    """Side-by-side A/B comparison of two builds across cost, AUW, T/W, endurance."""
    return _prompt_compare_builds(build_a_ids, build_b_ids)


@mcp.prompt()
def troubleshoot_build(part_ids: str, symptom: str) -> str:
    """Map a build symptom to likely causes via compat + physics."""
    return _prompt_troubleshoot_build(part_ids, symptom)


@mcp.prompt()
def endurance_what_if(
    airframe_id: str,
    battery_id: str,
    payload_weight_g: float = 0,
) -> str:
    """Endurance trade analysis: vary payload, compare batteries, compute range."""
    return _prompt_endurance_what_if(airframe_id, battery_id, payload_weight_g)


@mcp.prompt()
def upgrade_path(current_build_ids: str, goal: str) -> str:
    """Three-tier upgrade-swap recommendations toward a stated goal."""
    return _prompt_upgrade_path(current_build_ids, goal)


def _diagnostics() -> Dict[str, Any]:
    """Compact health + validation summary for ops use."""
    from .validation import full_validation_report
    from .catalog import load_parts_library

    library = load_parts_library()
    return {
        "version": __version__,
        "health": health(),
        "validation": full_validation_report(library),
    }


def main() -> None:
    import argparse
    import json as _json
    import sys

    parser = argparse.ArgumentParser(
        prog="architect-companion-mcp",
        description="Architect Companion MCP server (stdio).",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument(
        "--list-tools", action="store_true", help="List registered MCP tools and exit"
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Run catalog validation + health report and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return
    if args.list_tools:
        # FastMCP exposes registered tools through the underlying manager.
        try:
            tool_names = sorted(mcp._tool_manager._tools.keys())
        except AttributeError:
            tool_names = []
        for name in tool_names:
            print(name)
        return
    if args.diagnostics:
        _json.dump(_diagnostics(), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

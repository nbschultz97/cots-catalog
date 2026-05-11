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
from .physics import estimate_flight_time as _estimate_flight_time
from .recommend import recommend_configuration as _recommend_configuration
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

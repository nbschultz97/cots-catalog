"""HTTP gateway over the catalog + physics + wizard logic.

Wraps every domain function as a REST endpoint and serves the bundled
web UI at ``/``. The MCP server (``architect-companion-mcp``) stays
independent — the HTTP gateway is purely additive.

Optional dependency: install with ``pip install architect-companion-mcp[http]``.

Run with ``architect-companion-http`` (binds 127.0.0.1:8765 by default).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "architect-companion-mcp[http] not installed. "
        "Run: pip install architect-companion-mcp[http]"
    ) from exc

from . import __version__
from .blueprints import generate_mission_blueprint, list_operation_types, list_presets
from .catalog import (
    PART_CATEGORIES,
    catalog_stats,
    data_dir,
    list_components as cat_list,
    load_parts_library,
    part_by_id,
)
from .compatibility import check_compatibility
from .flight_data import (
    list_flight_records,
    submit_flight_record,
    validate_endurance_model,
)
from .physics import estimate_flight_time, estimate_range_km, estimate_thrust
from .recommend import recommend_configuration
from .templates import get_build_template, list_build_templates
from .validation import full_validation_report
from .wizard import build_wizard, suggest_alternatives


app = FastAPI(
    title="Architect Companion HTTP",
    description=(
        "REST gateway over the architect-companion-mcp catalog, "
        "physics, compatibility engine, and build wizard."
    ),
    version=__version__,
)

# Permissive CORS for web UI development. Tighten in production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request body models ----

class PartIDsBody(BaseModel):
    part_ids: List[str]


class RecommendBody(BaseModel):
    compute_tier: str = "pi5"
    mission_type: str = "long_range"
    budget_usd: Optional[float] = None


class WizardBody(BaseModel):
    mission_type: Optional[str] = None
    airframe_class: Optional[str] = None
    skill_level: Optional[str] = None
    budget_usd: Optional[float] = None
    top_n: int = 3


class FlightTimeBody(BaseModel):
    airframe_id: Optional[str] = None
    battery_id: Optional[str] = None
    platform_weight_g: Optional[float] = None
    platform_class: Optional[str] = None
    platform_type: str = "multi-rotor"
    prop_inches: Optional[float] = None
    battery_mah: Optional[float] = None
    battery_v: Optional[float] = None
    payload_weight_g: float = 0.0
    flight_mode: str = "hover"
    altitude_m: float = 0.0
    temperature_c: float = 15.0


class ThrustBody(BaseModel):
    airframe_id: str
    motor_id: str
    battery_id: str


class RangeBody(BaseModel):
    airframe_id: str
    battery_id: str
    cruise_speed_kmh: float = 60.0
    payload_weight_g: float = 0.0
    altitude_m: float = 0.0


class BlueprintBody(BaseModel):
    operation_type: str = "long_range"
    duration_hours: float = 24.0
    environment_id: Optional[str] = None
    team_size: int = 4


class AlternativesBody(BaseModel):
    failing_part_ids: List[str]
    issue: str
    top_n: int = 3


class FlightRecordBody(BaseModel):
    label: str
    observed_endurance_min: float
    build: Optional[List[str]] = None
    platform_weight_g: Optional[float] = None
    battery_mah: Optional[float] = None
    battery_v: Optional[float] = None
    payload_weight_g: float = 0
    flight_mode: str = "cruise"
    airframe_class: str = "unknown"
    source: str = "user_submission"
    notes: str = ""


# ---- Catalog endpoints ----

@app.get("/api/health")
def http_health():
    return {
        "status": "ok",
        "version": __version__,
        "service": "architect-companion-http",
        "data_dir": str(data_dir()),
        "catalog": catalog_stats(),
        "operation_types": list_operation_types(),
    }


@app.get("/api/categories")
def http_categories():
    return {"categories": list(PART_CATEGORIES)}


@app.get("/api/components")
def http_components(
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    tag: Optional[str] = None,
    availability: Optional[str] = None,
    max_weight_g: Optional[float] = None,
    max_cost_usd: Optional[float] = None,
    frequency_band: Optional[str] = None,
    limit: int = 100,
):
    return cat_list(
        category=category,
        manufacturer=manufacturer,
        tag=tag,
        availability=availability,
        max_weight_g=max_weight_g,
        max_cost_usd=max_cost_usd,
        frequency_band=frequency_band,
        limit=limit,
    )


@app.get("/api/parts/{part_id}")
def http_part(part_id: str):
    part = part_by_id(part_id)
    if not part:
        raise HTTPException(status_code=404, detail=f"Part '{part_id}' not found")
    return part


# ---- Compatibility + recommend + wizard ----

@app.post("/api/compatibility")
def http_compatibility(body: PartIDsBody):
    return check_compatibility(body.part_ids)


@app.post("/api/recommend")
def http_recommend(body: RecommendBody):
    return recommend_configuration(
        compute_tier=body.compute_tier,
        mission_type=body.mission_type,
        budget_usd=body.budget_usd,
    )


@app.post("/api/wizard")
def http_wizard(body: WizardBody):
    return build_wizard(
        mission_type=body.mission_type,
        airframe_class=body.airframe_class,
        skill_level=body.skill_level,
        budget_usd=body.budget_usd,
        top_n=body.top_n,
    )


@app.post("/api/alternatives")
def http_alternatives(body: AlternativesBody):
    return suggest_alternatives(
        failing_part_ids=body.failing_part_ids,
        issue=body.issue,
        top_n=body.top_n,
    )


# ---- Physics ----

@app.post("/api/flight-time")
def http_flight_time(body: FlightTimeBody):
    return estimate_flight_time(
        airframe_id=body.airframe_id,
        battery_id=body.battery_id,
        platform_weight_g=body.platform_weight_g,
        platform_class=body.platform_class,
        platform_type=body.platform_type,
        prop_inches=body.prop_inches,
        battery_mah=body.battery_mah,
        battery_v=body.battery_v,
        payload_weight_g=body.payload_weight_g,
        flight_mode=body.flight_mode,
        altitude_m=body.altitude_m,
        temperature_c=body.temperature_c,
    )


@app.post("/api/thrust")
def http_thrust(body: ThrustBody):
    return estimate_thrust(body.airframe_id, body.motor_id, body.battery_id)


@app.post("/api/range")
def http_range(body: RangeBody):
    return estimate_range_km(
        airframe_id=body.airframe_id,
        battery_id=body.battery_id,
        cruise_speed_kmh=body.cruise_speed_kmh,
        payload_weight_g=body.payload_weight_g,
        altitude_m=body.altitude_m,
    )


# ---- Templates ----

@app.get("/api/templates")
def http_templates(
    mission_type: Optional[str] = None,
    airframe_class: Optional[str] = None,
    skill_level: Optional[str] = None,
    max_budget_usd: Optional[float] = None,
):
    return list_build_templates(
        mission_type=mission_type,
        airframe_class=airframe_class,
        skill_level=skill_level,
        max_budget_usd=max_budget_usd,
    )


@app.get("/api/templates/{template_id}")
def http_template(template_id: str):
    try:
        return get_build_template(template_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---- Blueprints + presets ----

@app.post("/api/blueprint")
def http_blueprint(body: BlueprintBody):
    return generate_mission_blueprint(
        operation_type=body.operation_type,
        duration_hours=body.duration_hours,
        environment_id=body.environment_id,
        team_size=body.team_size,
    )


@app.get("/api/presets")
def http_presets():
    return list_presets()


# ---- Flight data + validation ----

@app.get("/api/flight-records")
def http_flight_records(airframe_class: Optional[str] = None, limit: int = 50):
    return list_flight_records(airframe_class=airframe_class, limit=limit)


@app.post("/api/flight-records")
def http_submit_flight_record(body: FlightRecordBody):
    return submit_flight_record(
        label=body.label,
        observed_endurance_min=body.observed_endurance_min,
        build=body.build,
        platform_weight_g=body.platform_weight_g,
        battery_mah=body.battery_mah,
        battery_v=body.battery_v,
        payload_weight_g=body.payload_weight_g,
        flight_mode=body.flight_mode,
        airframe_class=body.airframe_class,
        source=body.source,
        notes=body.notes,
    )


@app.post("/api/validate-endurance")
def http_validate_endurance(include_submissions: bool = True):
    return validate_endurance_model(include_submissions=include_submissions)


@app.get("/api/validate-catalog")
def http_validate_catalog():
    return full_validation_report(load_parts_library())


# ---- Web UI static serving ----

WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "web"


@app.get("/")
def http_root():
    index = WEB_ROOT / "index.html"
    if not index.exists():
        return HTMLResponse(
            f"<h1>architect-companion-http v{__version__}</h1>"
            "<p>API is live. See <a href='/docs'>/docs</a> for the OpenAPI schema.</p>"
            "<p>The web UI is not bundled in this install. Source: "
            "<a href='https://github.com/nbschultz97/cots-catalog'>nbschultz97/cots-catalog</a></p>"
        )
    return FileResponse(index)


# Mount /web/* for any static assets the UI references (CSS, JS, images).
if WEB_ROOT.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_ROOT)), name="web")


def main() -> None:
    """CLI entry: ``architect-companion-http`` runs uvicorn."""
    import uvicorn

    parser = argparse.ArgumentParser(
        prog="architect-companion-http",
        description="HTTP gateway over the Architect Companion catalog + physics.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    uvicorn.run(
        "architect_companion_mcp.http_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

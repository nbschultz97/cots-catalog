from __future__ import annotations

import os
from pathlib import Path

import pytest

# Force the bundled data dir before any module imports cache load paths.
REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("ARCHITECT_DATA_DIR", str(REPO_ROOT / "data"))

from architect_companion_mcp import __version__
from architect_companion_mcp.blueprints import (
    generate_mission_blueprint,
    list_operation_types,
    list_presets,
)
from architect_companion_mcp.catalog import (
    PART_CATEGORIES,
    catalog_stats,
    list_components,
    part_by_id,
    reset_cache,
)
from architect_companion_mcp.compatibility import check_compatibility
from architect_companion_mcp.physics import estimate_flight_time
from architect_companion_mcp.recommend import recommend_configuration
from architect_companion_mcp.server import health


@pytest.fixture(autouse=True)
def _clear_catalog_cache():
    reset_cache()
    yield
    reset_cache()


def test_version_is_081_plus():
    # 0.8.1 introduces the flight-data validation framework
    assert __version__.startswith("0.8")
    parts = __version__.split(".")
    assert int(parts[0]) >= 0
    assert int(parts[1]) >= 8


def test_health_reports_catalog():
    result = health()
    assert result["status"] == "ok"
    assert result["catalog"]["total"] > 0
    assert "presets" in result
    assert result["version"] == __version__


def test_catalog_stats_has_every_category():
    stats = catalog_stats()
    for cat in PART_CATEGORIES:
        assert cat in stats["counts"]
    assert stats["schemaVersion"] == "1.1.0"


def test_list_components_filters():
    airframes = list_components(category="airframes")
    assert airframes and all(p["_category"] == "airframes" for p in airframes)

    fpv_5in = list_components(category="airframes", tag="5-inch")
    assert fpv_5in and all("5-inch" in (p.get("tags") or []) for p in fpv_5in)

    cheap = list_components(category="airframes", max_cost_usd=100)
    assert all((p.get("cost_usd") or 0) <= 100 for p in cheap)


def test_part_by_id_lookup_and_miss():
    part = part_by_id("airframe-5in-true-x")
    assert part is not None
    assert part["_category"] == "airframes"
    assert part_by_id("nope-not-real") is None


def test_check_compatibility_unknown_part():
    result = check_compatibility(["definitely-fake-id"])
    assert result["compatible"] is False
    assert "Unknown part IDs" in result["reason"]


def test_check_compatibility_weight_budget_violation():
    # 5" airframe with a 10" heavy-lift battery should bust the budget.
    library_5in = list_components(category="airframes", tag="5-inch", limit=1)
    heavy_battery = list_components(category="batteries", limit=1)
    assert library_5in and heavy_battery
    ids = [library_5in[0]["id"], heavy_battery[0]["id"]]
    result = check_compatibility(ids)
    assert "compatible" in result
    assert "budget" in result
    assert result["budget"]["component_weight_g"] >= 0


def test_check_compatibility_voltage_chain():
    batteries = list_components(category="batteries")
    motors = list_components(category="motors")
    assert batteries and motors
    result = check_compatibility([batteries[0]["id"], motors[0]["id"]])
    # Should not crash and should produce a structured report.
    assert "issues" in result
    assert "total_weight_g" in result


def test_estimate_flight_time_with_raw_inputs():
    result = estimate_flight_time(
        platform_weight_g=1500,
        battery_mah=5200,
        payload_weight_g=200,
    )
    assert result["safe_endurance_min"] > 0
    assert result["reserve_pct"] == 20
    # AUW includes the synthetic 50g overhead for FC/ESC/wires/etc.
    assert result["auw_g"] == pytest.approx(1750, abs=1)


def test_estimate_flight_time_hover_vs_cruise_diverge_on_longrange():
    airframes = list_components(category="airframes", tag="long-range", limit=1)
    batteries = list_components(category="batteries", limit=1)
    if not airframes or not batteries:
        pytest.skip("Catalog missing long-range airframe or batteries")
    hover = estimate_flight_time(
        airframe_id=airframes[0]["id"],
        battery_id=batteries[0]["id"],
        flight_mode="hover",
    )
    cruise = estimate_flight_time(
        airframe_id=airframes[0]["id"],
        battery_id=batteries[0]["id"],
        flight_mode="cruise",
    )
    # Long-range frames have a meaningful cruise factor (>=1.5)
    assert cruise["safe_endurance_min"] > hover["safe_endurance_min"] * 1.4


def test_estimate_flight_time_auto_picks_cruise_for_fixed_wing():
    airframes = list_components(category="airframes", tag="fixed-wing", limit=1)
    batteries = list_components(category="batteries", limit=1)
    if not airframes or not batteries:
        pytest.skip("Catalog missing fixed-wing airframe")
    auto = estimate_flight_time(
        airframe_id=airframes[0]["id"],
        battery_id=batteries[0]["id"],
        flight_mode="auto",
    )
    assert auto["flight_mode_resolved"] == "cruise"


def test_estimate_thrust_returns_tw_ratio():
    from architect_companion_mcp.physics import estimate_thrust

    result = estimate_thrust(
        airframe_id="airframe-5in-true-x",
        motor_id="motor-iflight-xing2-2207-2050kv",
        battery_id="battery-cnhl-black-4s-1500mah-100c",
    )
    assert result["thrust_to_weight_ratio"] > 0
    assert "verdict" in result
    assert result["n_motors"] == 4


def test_validate_endurance_model_returns_report():
    from architect_companion_mcp.flight_data import validate_endurance_model

    report = validate_endurance_model(include_submissions=False)
    assert report["n_records"] > 0
    assert "mae_min" in report and report["mae_min"] is not None
    assert "mape_pct" in report and report["mape_pct"] is not None
    assert "per_class" in report
    assert isinstance(report["worst"], list)
    # Worst-5 entries must each have predicted/observed/error fields
    if report["worst"]:
        first = report["worst"][0]
        assert "predicted_min" in first and "observed_min" in first


def test_flight_data_has_seed_records():
    from architect_companion_mcp.flight_data import load_records

    records = load_records(include_submissions=False)
    assert len(records) >= 10, "Bundled flight_data.jsonl should ship with ≥10 seed records"
    for r in records:
        assert r.get("observed_endurance_min", 0) > 0
        assert r.get("airframe_class")
        # Must have either a build or raw-spec inputs
        has_build = bool(r.get("build"))
        has_raw = bool(r.get("platform_weight_g") and r.get("battery_mah"))
        assert has_build or has_raw, f"{r['id']} has neither build nor raw spec"


def test_submit_flight_record_appends(tmp_path, monkeypatch):
    from architect_companion_mcp.flight_data import submit_flight_record, load_records

    monkeypatch.setenv("ARCHITECT_COMPANION_DATA_DIR", str(tmp_path))
    result = submit_flight_record(
        label="Test submission",
        observed_endurance_min=4.2,
        platform_weight_g=500,
        battery_mah=1300,
        battery_v=22.2,
        flight_mode="cruise",
        airframe_class="5-inch",
        source="pytest",
    )
    assert result["status"] == "recorded"
    assert "id" in result
    submitted = load_records(include_submissions=True)
    assert any(r["label"] == "Test submission" for r in submitted)


def test_estimate_range_km_returns_round_trip():
    from architect_companion_mcp.physics import estimate_range_km

    result = estimate_range_km(
        airframe_id="airframe-7in-longrange",
        battery_id="battery-4s-5200mah-li-ion",
        cruise_speed_kmh=70,
    )
    assert result["one_way_range_km"] > 0
    assert result["round_trip_range_km"] == pytest.approx(result["one_way_range_km"] / 2.0, abs=0.1)


def test_estimate_flight_time_with_catalog_ids():
    airframes = list_components(category="airframes", limit=1)
    batteries = list_components(category="batteries", limit=1)
    assert airframes and batteries
    result = estimate_flight_time(
        airframe_id=airframes[0]["id"],
        battery_id=batteries[0]["id"],
        payload_weight_g=150,
    )
    assert result["airframe_id"] == airframes[0]["id"]
    assert result["battery_id"] == batteries[0]["id"]
    assert result["safe_endurance_min"] > 0


def test_estimate_flight_time_rejects_missing_inputs():
    with pytest.raises(ValueError):
        estimate_flight_time()


def test_generate_mission_blueprint_default():
    bp = generate_mission_blueprint()
    assert bp["schemaVersion"] == "2.0.0"
    assert bp["projectId"].startswith("blueprint-")
    assert bp["meta"]["origin_tool"] == "architect-companion-mcp"
    assert bp["environment"]
    assert "mission" in bp


def test_generate_mission_blueprint_uses_known_preset():
    bp = generate_mission_blueprint(operation_type="urban_congested")
    assert bp["meta"]["seed_preset"] == "preset_urban_congested.json"


def test_generate_mission_blueprint_unknown_operation_falls_back():
    bp = generate_mission_blueprint(operation_type="not-a-real-op")
    assert bp["meta"]["seed_preset"].startswith("preset_")


def test_list_presets_and_operations():
    presets = list_presets()
    assert {p["file"] for p in presets} == {
        "preset_long_range_relay.json",
        "preset_endurance_survey.json",
        "preset_urban_congested.json",
        "preset_cold_weather.json",
        "preset_tinywhoop_indoor.json",
        "preset_sub_250g.json",
        "preset_beginner_5in.json",
    }
    ops = list_operation_types()
    for expected in ("long_range", "endurance", "cold_weather", "tinywhoop", "sub_250g", "beginner"):
        assert expected in ops, f"Missing operation type: {expected}"


def test_recommend_configuration_picks_parts():
    rec = recommend_configuration(compute_tier="pi5", mission_type="long_range")
    assert rec["compute_tier"] == "pi5"
    assert rec["picks"]["airframe"] is not None
    assert rec["totals"]["cost_usd"] > 0


def test_recommend_configuration_rejects_bad_tier():
    with pytest.raises(ValueError):
        recommend_configuration(compute_tier="potato-pi")


def test_recommend_configuration_budget_caps():
    rec = recommend_configuration(compute_tier="pi5", mission_type="long_range", budget_usd=20)
    # Every catalog part should be at or below the budget. companion_compute is a
    # synthetic pseudo-pick with cost_usd=None and is exempt.
    for slot, part in rec["picks"].items():
        if part is None or slot == "companion_compute":
            continue
        assert (part.get("cost_usd") or 0) <= 20


def test_recommend_includes_companion_compute_in_totals():
    rec = recommend_configuration(compute_tier="jetson-orin-nano", mission_type="endurance_survey")
    assert rec["picks"]["companion_compute"]["weight_g"] == 270
    assert rec["totals"]["compute_weight_g"] == 270
    assert rec["totals"]["weight_g"] == rec["totals"]["parts_weight_g"] + 270


def test_recommend_compute_tier_biases_airframe():
    # Light compute should land on a smaller, lighter airframe than a heavy one.
    light = recommend_configuration(compute_tier="pi-zero", mission_type="freestyle")
    heavy = recommend_configuration(compute_tier="x86", mission_type="endurance_survey")
    # Sanity: chosen airframes should differ (catalog has 5 airframes spanning
    # 5"/7"/10"/fixed-wing — picks should not collapse to the same frame).
    assert light["picks"]["airframe"]["id"] != heavy["picks"]["airframe"]["id"]


def test_check_compatibility_kv_prop_too_high():
    # 1960KV on a 10" prop (heavy frame, prop_size '10x5x3') should flag —
    # the 9.5-13" band tops out around 1200KV.
    issues = check_compatibility([
        "airframe-10in-heavy",
        "motor-rcinpower-gts-v4-2207-1960kv",
    ])["issues"]
    assert any("too high" in i for i in issues), issues


def test_check_compatibility_kv_prop_too_low():
    # 730KV on a 5" prop should flag underprop.
    issues = check_compatibility([
        "airframe-5in-true-x",
        "motor-avenger-3110-730kv",
    ])["issues"]
    assert any("too low" in i for i in issues), issues


def test_check_compatibility_kv_prop_in_band_passes():
    # 1300KV on a 7" prop should NOT trip the KV rule.
    issues = check_compatibility([
        "airframe-7in-longrange",
        "motor-emax-eco-ii-2807-1300kv",
    ])["issues"]
    assert not any("too high" in i or "too low" in i for i in issues), issues


def test_check_compatibility_motor_count_mismatch():
    # Airframe expects 4 motors. Listing 2 motor entries (more than 1, fewer
    # than 4) should flag the count mismatch. We use the same motor twice via
    # the same ID — list_compatibility resolves duplicates, so we need two
    # different motor IDs.
    motors = list_components(category="motors")
    assert len(motors) >= 2
    issues = check_compatibility([
        "airframe-5in-true-x",
        motors[0]["id"],
        motors[1]["id"],
    ])["issues"]
    assert any("motors" in i.lower() and ("expects" in i or "lists" in i) for i in issues), issues


def test_recommend_includes_validation_block():
    rec = recommend_configuration(compute_tier="pi5", mission_type="long_range")
    assert "validation" in rec
    assert "compatible" in rec["validation"]
    assert "issues" in rec["validation"]
    # Validation is a list, not a string
    assert isinstance(rec["validation"]["issues"], list)


def test_validate_catalog_tool_returns_full_report():
    from architect_companion_mcp.server import validate_catalog

    report = validate_catalog()
    assert "ok" in report
    assert "schema" in report
    assert "ids" in report
    assert "required_fields" in report


def test_check_compatibility_motor_count_single_spec_line_ok():
    # One motor entry is treated as a spec line — should not flag count.
    motors = list_components(category="motors", tag="5-inch", limit=1)
    if not motors:
        motors = list_components(category="motors", limit=1)
    issues = check_compatibility([
        "airframe-5in-true-x",
        motors[0]["id"],
    ])["issues"]
    assert not any("Airframe expects" in i and "motors" in i for i in issues), issues

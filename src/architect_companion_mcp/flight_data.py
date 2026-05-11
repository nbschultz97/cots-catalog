"""Real flight-data ground truth for calibrating the endurance model.

The bundled ``data/flight_data.jsonl`` holds community-submitted and
published flight records — each one a real "I built this kit and flew
for X minutes" data point. The :func:`validate_endurance_model`
function runs the model against every record and reports per-class
accuracy so we can see where the physics needs more calibration.

This is the credibility moat vs closed tools like eCalc — the ground
truth is open, auditable, and grows with the community.

## Record schema

Each line is one JSON object:

.. code-block:: json

    {
      "id": "fd-bardwell-5in-6s-1300-100c",
      "submitted_at": "2026-05-11T10:00:00Z",
      "label": "Bardwell-style 5\\" freestyle, 6S 1300mAh 100C",
      "build": ["airframe-5in-true-x", "battery-gnb-6s-1300mah-120c", ...],
      "platform_weight_g": null,
      "battery_mah": null,
      "battery_v": null,
      "payload_weight_g": 0,
      "flight_mode": "cruise",
      "observed_endurance_min": 3.5,
      "observed_endurance_min_low": 3.0,
      "observed_endurance_min_high": 4.0,
      "conditions": {"altitude_m": 300, "temperature_c": 20, "wind_kmh": 5},
      "airframe_class": "5-inch",
      "source": "https://www.youtube.com/@JoshuaBardwell",
      "source_type": "youtube_creator_consensus",
      "notes": "Aggressive freestyle cruise; consistent across multiple Bardwell videos."
    }

Either ``build`` (catalog part IDs) or the raw ``platform_weight_g`` +
``battery_mah`` (+ ``battery_v``) fields must be populated. The model
runner picks the right path automatically.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .catalog import data_dir, part_by_id
from .physics import estimate_flight_time


def flight_data_path() -> Path:
    """Bundled ground-truth file path."""
    return data_dir() / "flight_data.jsonl"


def runtime_submissions_path() -> Path:
    """User submissions land here so the bundled file stays clean."""
    import os
    root = Path(os.environ.get("ARCHITECT_COMPANION_DATA_DIR", "./runtime_data"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "flight_data_submissions.jsonl"


def load_records(include_submissions: bool = True) -> List[Dict[str, Any]]:
    """Load all flight-data records (bundled + optional user submissions)."""
    records: List[Dict[str, Any]] = []
    bundled = flight_data_path()
    if bundled.exists():
        for line in bundled.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    if include_submissions:
        submissions = runtime_submissions_path()
        if submissions.exists():
            for line in submissions.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    return records


def _run_model_for_record(record: Dict[str, Any]) -> Optional[float]:
    """Run estimate_flight_time against a record's build manifest.

    Returns predicted endurance in minutes, or None if the record's
    referenced parts can't all be resolved.
    """
    build = record.get("build") or []
    airframe_id = next(
        (pid for pid in build if (p := part_by_id(pid)) and p["_category"] == "airframes"),
        None,
    )
    battery_id = next(
        (pid for pid in build if (p := part_by_id(pid)) and p["_category"] == "batteries"),
        None,
    )

    kwargs: Dict[str, Any] = {
        "payload_weight_g": float(record.get("payload_weight_g") or 0),
        "flight_mode": record.get("flight_mode", "cruise"),
    }
    conditions = record.get("conditions") or {}
    if "altitude_m" in conditions:
        kwargs["altitude_m"] = float(conditions["altitude_m"])
    if "temperature_c" in conditions:
        kwargs["temperature_c"] = float(conditions["temperature_c"])

    if airframe_id and battery_id:
        result = estimate_flight_time(airframe_id=airframe_id, battery_id=battery_id, **kwargs)
        return float(result["safe_endurance_min"])

    # Raw-spec path — used when build references parts not in our catalog
    if record.get("platform_weight_g") and record.get("battery_mah"):
        result = estimate_flight_time(
            platform_weight_g=float(record["platform_weight_g"]),
            battery_mah=float(record["battery_mah"]),
            battery_v=float(record["battery_v"]) if record.get("battery_v") else None,
            **kwargs,
        )
        return float(result["safe_endurance_min"])

    return None


def validate_endurance_model(include_submissions: bool = True) -> Dict[str, Any]:
    """Run the endurance model against every flight-data record and
    return per-class accuracy.

    Returns a dict with:

    - ``n_records`` — total records evaluated.
    - ``mae_min`` — mean absolute error in minutes across all records.
    - ``mape_pct`` — mean absolute percentage error.
    - ``per_class`` — per-airframe-class breakdown (n, MAE, MAPE).
    - ``worst`` — top 5 records where the model is furthest from observed.
    - ``records`` — per-record predicted vs observed + error.
    """
    records = load_records(include_submissions=include_submissions)
    per_class: Dict[str, List[Dict[str, float]]] = {}
    all_errors_min: List[float] = []
    all_errors_pct: List[float] = []
    detailed: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for rec in records:
        observed = float(rec.get("observed_endurance_min") or 0)
        if observed <= 0:
            skipped.append(f"{rec.get('id', '?')}: missing observed_endurance_min")
            continue
        try:
            predicted = _run_model_for_record(rec)
        except Exception as exc:  # noqa: BLE001
            skipped.append(f"{rec.get('id', '?')}: model error — {exc}")
            continue
        if predicted is None:
            skipped.append(f"{rec.get('id', '?')}: parts not resolvable")
            continue

        err_min = predicted - observed
        err_pct = (err_min / observed) * 100.0
        all_errors_min.append(abs(err_min))
        all_errors_pct.append(abs(err_pct))

        airframe_class = rec.get("airframe_class") or "unknown"
        per_class.setdefault(airframe_class, []).append({
            "abs_err_min": abs(err_min),
            "abs_err_pct": abs(err_pct),
        })

        detailed.append({
            "id": rec.get("id"),
            "label": rec.get("label"),
            "airframe_class": airframe_class,
            "predicted_min": round(predicted, 1),
            "observed_min": observed,
            "error_min": round(err_min, 1),
            "error_pct": round(err_pct, 1),
            "source": rec.get("source"),
        })

    detailed_sorted = sorted(detailed, key=lambda d: abs(d["error_pct"]), reverse=True)

    per_class_summary: Dict[str, Dict[str, float]] = {}
    for cls, errs in per_class.items():
        if not errs:
            continue
        per_class_summary[cls] = {
            "n": len(errs),
            "mae_min": round(statistics.mean(e["abs_err_min"] for e in errs), 2),
            "mape_pct": round(statistics.mean(e["abs_err_pct"] for e in errs), 1),
        }

    return {
        "n_records": len(detailed),
        "n_skipped": len(skipped),
        "mae_min": round(statistics.mean(all_errors_min), 2) if all_errors_min else None,
        "mape_pct": round(statistics.mean(all_errors_pct), 1) if all_errors_pct else None,
        "per_class": per_class_summary,
        "worst": detailed_sorted[:5],
        "records": detailed,
        "skipped": skipped,
    }


def submit_flight_record(
    label: str,
    observed_endurance_min: float,
    *,
    build: Optional[List[str]] = None,
    platform_weight_g: Optional[float] = None,
    battery_mah: Optional[float] = None,
    battery_v: Optional[float] = None,
    payload_weight_g: float = 0,
    flight_mode: str = "cruise",
    airframe_class: str = "unknown",
    source: str = "user_submission",
    source_type: str = "user_submission",
    notes: str = "",
    conditions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Append a new flight-data record to the runtime submissions file.

    Submissions go to ``ARCHITECT_COMPANION_DATA_DIR`` (defaults to
    ``./runtime_data``), not the bundled file — keeps the public catalog
    clean while letting users grow their local ground truth.
    """
    if not build and (platform_weight_g is None or battery_mah is None):
        raise ValueError(
            "Must supply either a catalog `build` list or "
            "`platform_weight_g + battery_mah`."
        )

    record_id = f"fd-{int(datetime.now(timezone.utc).timestamp())}"
    record = {
        "id": record_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "build": build or [],
        "platform_weight_g": platform_weight_g,
        "battery_mah": battery_mah,
        "battery_v": battery_v,
        "payload_weight_g": payload_weight_g,
        "flight_mode": flight_mode,
        "observed_endurance_min": observed_endurance_min,
        "conditions": conditions or {},
        "airframe_class": airframe_class,
        "source": source,
        "source_type": source_type,
        "notes": notes,
    }
    path = runtime_submissions_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    return {"status": "recorded", "id": record_id, "path": str(path)}


def list_flight_records(
    airframe_class: Optional[str] = None,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Browse flight-data records with an optional class filter."""
    records = load_records(include_submissions=True)
    if airframe_class:
        records = [r for r in records if r.get("airframe_class") == airframe_class]
    out: List[Dict[str, Any]] = []
    for rec in records[:limit]:
        out.append({
            "id": rec.get("id"),
            "label": rec.get("label"),
            "airframe_class": rec.get("airframe_class"),
            "observed_endurance_min": rec.get("observed_endurance_min"),
            "flight_mode": rec.get("flight_mode"),
            "source": rec.get("source"),
            "build": rec.get("build"),
        })
    return out

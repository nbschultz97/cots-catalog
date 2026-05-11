"""Optional JSON Schema validation for the parts library.

``jsonschema`` is an optional install (``pip install
architect-companion-mcp[schema]``). If unavailable, validation is a
no-op so the MCP server still starts in lean environments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _schema_path() -> Path:
    """Resolve the bundled parts_library schema path."""
    from .catalog import data_dir

    return data_dir() / "schema" / "parts_library_schema.json"


def validate_parts_library(library: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Return ``(ok, errors)``. Empty error list ⇒ valid (or jsonschema
    not installed, in which case validation is skipped)."""

    try:
        from jsonschema import Draft7Validator
    except ImportError:
        return True, []

    schema_path = _schema_path()
    if not schema_path.exists():
        return True, [f"Schema not found at {schema_path}; skipped validation."]

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft7Validator(schema)
    errors: List[str] = []
    for err in sorted(validator.iter_errors(library), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return len(errors) == 0, errors


def validate_part_ids_unique(library: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Every category's parts must have unique IDs."""
    from .catalog import PART_CATEGORIES

    issues: List[str] = []
    seen_global: Dict[str, str] = {}
    for category in PART_CATEGORIES:
        seen: Dict[str, int] = {}
        for part in library.get(category, []):
            pid = part.get("id")
            if not pid:
                issues.append(f"{category}: part missing id field")
                continue
            seen[pid] = seen.get(pid, 0) + 1
            if pid in seen_global and seen_global[pid] != category:
                issues.append(
                    f"id '{pid}' appears in both {seen_global[pid]} and {category}"
                )
            seen_global[pid] = category
        for pid, count in seen.items():
            if count > 1:
                issues.append(f"{category}: duplicate id '{pid}' ({count} times)")
    return len(issues) == 0, issues


def required_fields_for(category: str) -> List[str]:
    """Per-category required fields the catalog quality test enforces."""
    base = ["id", "name", "weight_g"]
    extras = {
        "airframes": ["type"],
        "motors": ["kv", "max_thrust_g"],
        "escs": ["max_current_a"],
        "batteries": ["chemistry", "voltage_nominal_v", "capacity_mah"],
        "flight_controllers": [],
        "radios": ["type", "frequency_band"],
        "sensors": ["type"],
        "accessories": ["category"],
    }
    return base + extras.get(category, [])


def validate_required_fields(library: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Each part must have category-specific required fields populated."""
    from .catalog import PART_CATEGORIES

    issues: List[str] = []
    for category in PART_CATEGORIES:
        required = required_fields_for(category)
        for part in library.get(category, []):
            for field in required:
                if part.get(field) in (None, "", []):
                    issues.append(
                        f"{category}/{part.get('id', '<no-id>')}: missing required '{field}'"
                    )
    return len(issues) == 0, issues


def full_validation_report(library: Dict[str, Any]) -> Dict[str, Any]:
    """Combined validation: schema + unique IDs + required fields."""
    schema_ok, schema_errors = validate_parts_library(library)
    ids_ok, id_issues = validate_part_ids_unique(library)
    fields_ok, field_issues = validate_required_fields(library)
    return {
        "ok": schema_ok and ids_ok and fields_ok,
        "schema": {"ok": schema_ok, "errors": schema_errors},
        "ids": {"ok": ids_ok, "issues": id_issues},
        "required_fields": {"ok": fields_ok, "issues": field_issues},
    }

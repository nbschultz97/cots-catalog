"""MCP Resources — read-only catalog URIs the LLM can browse without
tool calls.

URI schemes:

* ``catalog://stats`` — catalog summary (counts, schema versions).
* ``catalog://categories/{category}`` — full list of parts in a category.
* ``catalog://parts/{part_id}`` — a single part by ID.
* ``catalog://presets`` — list of available mission presets.
* ``catalog://presets/{filename}`` — full body of a preset.
* ``schema://parts_library`` — JSON schema for the parts library.
* ``schema://mission_project`` — JSON schema for MissionProject v2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .catalog import (
    PART_CATEGORIES,
    PRESET_FILES,
    catalog_stats,
    data_dir,
    load_parts_library,
    load_preset,
    part_by_id,
)


def stats_resource() -> str:
    return json.dumps(catalog_stats(), indent=2)


def category_resource(category: str) -> str:
    if category not in PART_CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    library = load_parts_library()
    return json.dumps(library.get(category, []), indent=2)


def part_resource(part_id: str) -> str:
    part = part_by_id(part_id)
    if part is None:
        raise ValueError(f"Part '{part_id}' not found")
    return json.dumps(part, indent=2)


def preset_index_resource() -> str:
    out = []
    for filename in PRESET_FILES:
        preset = load_preset(filename)
        out.append({
            "file": filename,
            "projectId": preset.get("projectId"),
            "name": preset.get("meta", {}).get("name"),
            "missionType": preset.get("meta", {}).get("missionType"),
            "durationHours": preset.get("meta", {}).get("durationHours"),
        })
    return json.dumps(out, indent=2)


def preset_resource(filename: str) -> str:
    return json.dumps(load_preset(filename), indent=2)


def schema_resource(schema_name: str) -> str:
    schema_dir = data_dir() / "schema"
    if schema_name == "parts_library":
        path = schema_dir / "parts_library_schema.json"
    elif schema_name == "mission_project":
        path = schema_dir / "mission_project_schema_v2.json"
    else:
        raise ValueError(f"Unknown schema: {schema_name}")
    return path.read_text(encoding="utf-8")

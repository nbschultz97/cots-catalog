"""Parts library, presets, and environment taxonomy loaders.

Reads JSON files conforming to the COTS-Architect schemas
(parts_library_schema v1.1.0, mission_project_schema v2.0.0).
Data directory resolution order:

1. ``ARCHITECT_DATA_DIR`` environment variable, if set.
2. ``<package>/../../data`` (the repo-vendored copy of COTS-Architect data).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PART_CATEGORIES = (
    "airframes",
    "motors",
    "escs",
    "batteries",
    "flight_controllers",
    "radios",
    "sensors",
    "accessories",
)

PRESET_FILES = (
    "preset_low_infrastructure.json",
    "preset_partner_sustainment.json",
    "preset_urban_high_ew.json",
    "preset_whitefrost.json",
)


def data_dir() -> Path:
    override = os.environ.get("ARCHITECT_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent.parent / "data").resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_parts_library() -> Dict[str, Any]:
    return _load_json(data_dir() / "parts_library.json")


@lru_cache(maxsize=1)
def load_environment_taxonomy() -> Dict[str, Any]:
    return _load_json(data_dir() / "environment_taxonomy.json")


@lru_cache(maxsize=None)
def load_preset(filename: str) -> Dict[str, Any]:
    if filename not in PRESET_FILES:
        raise KeyError(f"Unknown preset: {filename}. Available: {PRESET_FILES}")
    return _load_json(data_dir() / filename)


def all_presets() -> Dict[str, Dict[str, Any]]:
    return {name: load_preset(name) for name in PRESET_FILES}


def reset_cache() -> None:
    load_parts_library.cache_clear()
    load_environment_taxonomy.cache_clear()
    load_preset.cache_clear()


def part_by_id(part_id: str) -> Optional[Dict[str, Any]]:
    """Find a part by ID across every category. Returns the part dict with
    an injected ``_category`` field, or None if not found."""
    library = load_parts_library()
    for category in PART_CATEGORIES:
        for part in library.get(category, []):
            if part.get("id") == part_id:
                return {**part, "_category": category}
    return None


def list_components(
    category: Optional[str] = None,
    *,
    manufacturer: Optional[str] = None,
    tag: Optional[str] = None,
    availability: Optional[str] = None,
    max_weight_g: Optional[float] = None,
    max_cost_usd: Optional[float] = None,
    frequency_band: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Browse the COTS parts library with optional filters.

    ``category`` is one of :data:`PART_CATEGORIES`. Filters are AND-combined.
    Each returned record is annotated with ``_category``.
    """

    library = load_parts_library()

    if category and category not in PART_CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. Valid: {', '.join(PART_CATEGORIES)}"
        )

    categories: Iterable[str] = (category,) if category else PART_CATEGORIES

    out: List[Dict[str, Any]] = []
    for cat in categories:
        for part in library.get(cat, []):
            if manufacturer and manufacturer.lower() not in (part.get("manufacturer") or "").lower():
                continue
            if tag and tag not in (part.get("tags") or []):
                continue
            if availability and part.get("availability") != availability:
                continue
            if max_weight_g is not None and (part.get("weight_g") or 0) > max_weight_g:
                continue
            if max_cost_usd is not None and (part.get("cost_usd") or 0) > max_cost_usd:
                continue
            if frequency_band and part.get("frequency_band") != frequency_band:
                continue
            out.append({**part, "_category": cat})
            if limit and len(out) >= limit:
                return out
    return out


def catalog_stats() -> Dict[str, Any]:
    library = load_parts_library()
    counts = {cat: len(library.get(cat, [])) for cat in PART_CATEGORIES}
    return {
        "catalogId": library.get("catalogId"),
        "schemaVersion": library.get("schemaVersion"),
        "name": library.get("meta", {}).get("name"),
        "counts": counts,
        "total": sum(counts.values()),
    }

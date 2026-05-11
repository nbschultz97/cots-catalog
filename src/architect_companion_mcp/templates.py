"""Build template registry — curated canonical builds the LLM can pick
from in one shot. Each template lists a complete kit of catalog part IDs
plus mission, skill level, and budget estimate. Pair with the wizard
and alternatives tools to iterate from a template baseline.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from .catalog import data_dir


@lru_cache(maxsize=1)
def load_templates() -> Dict[str, Any]:
    path = data_dir() / "build_templates.json"
    if not path.exists():
        return {"schemaVersion": "1.0.0", "templates": []}
    return json.loads(path.read_text(encoding="utf-8"))


def reset_cache() -> None:
    load_templates.cache_clear()


def list_build_templates(
    mission_type: Optional[str] = None,
    airframe_class: Optional[str] = None,
    skill_level: Optional[str] = None,
    max_budget_usd: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Browse curated build templates with filters."""
    templates = load_templates().get("templates", [])
    out: List[Dict[str, Any]] = []
    for tpl in templates:
        if mission_type and tpl.get("mission_type") != mission_type:
            continue
        if airframe_class and tpl.get("airframe_class") != airframe_class:
            continue
        if skill_level and tpl.get("skill_level") != skill_level:
            continue
        if max_budget_usd is not None and (tpl.get("budget_estimate_usd") or 0) > max_budget_usd:
            continue
        out.append({
            "id": tpl["id"],
            "name": tpl["name"],
            "mission_type": tpl.get("mission_type"),
            "airframe_class": tpl.get("airframe_class"),
            "skill_level": tpl.get("skill_level"),
            "budget_estimate_usd": tpl.get("budget_estimate_usd"),
            "description": tpl.get("description"),
        })
    return out


def get_build_template(template_id: str) -> Dict[str, Any]:
    """Fetch a complete build template by ID."""
    for tpl in load_templates().get("templates", []):
        if tpl["id"] == template_id:
            return tpl
    raise KeyError(f"Build template '{template_id}' not found")


def template_part_ids(template: Dict[str, Any]) -> List[str]:
    """Flatten a template's parts dict into a list of catalog part IDs."""
    return [pid for pid in template.get("parts", {}).values() if pid]

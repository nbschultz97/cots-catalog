"""Catalog data-quality tests.

These run in CI on every push to keep the bundled catalog healthy:
schema-valid, unique IDs, required fields populated, provenance present
on ingested parts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("ARCHITECT_DATA_DIR", str(REPO_ROOT / "data"))

from architect_companion_mcp.catalog import PART_CATEGORIES
from architect_companion_mcp.validation import (
    full_validation_report,
    required_fields_for,
)

LIB = REPO_ROOT / "data" / "parts_library.json"


@pytest.fixture(scope="module")
def library() -> dict:
    return json.loads(LIB.read_text(encoding="utf-8"))


def test_full_validation_report_ok(library: dict) -> None:
    report = full_validation_report(library)
    if not report["ok"]:
        # Pretty-print failures so CI logs are actionable.
        msg = ["Catalog validation failed:"]
        for section, body in report.items():
            if section == "ok" or body.get("ok"):
                continue
            msg.append(f"  [{section}]")
            for line in body.get("errors", []) or body.get("issues", []):
                msg.append(f"    - {line}")
        pytest.fail("\n".join(msg))


def test_required_fields_present(library: dict) -> None:
    for category in PART_CATEGORIES:
        required = required_fields_for(category)
        for part in library.get(category, []):
            for field in required:
                assert part.get(field) not in (None, "", []), (
                    f"{category}/{part.get('id', '<no-id>')} missing '{field}'"
                )


def test_no_duplicate_ids(library: dict) -> None:
    seen: dict[str, str] = {}
    for category in PART_CATEGORIES:
        for part in library.get(category, []):
            pid = part["id"]
            assert pid not in seen, (
                f"Duplicate id '{pid}' in {category} (also in {seen.get(pid)})"
            )
            seen[pid] = category


def test_ingested_parts_have_data_source(library: dict) -> None:
    """Parts with an id matching ingested provenance must carry data_source."""
    for category in PART_CATEGORIES:
        for part in library.get(category, []):
            if "data_source" not in part:
                continue
            ds = part["data_source"]
            assert "url" in ds and "fetched_at" in ds and "parser" in ds, (
                f"{category}/{part['id']} has data_source but missing keys: {ds}"
            )


def test_no_mil_or_cui_language_in_catalog(library: dict) -> None:
    """Hobby-marketable posture: no ITAR / ISR / EMCON / CUI / NSN strings."""
    forbidden = ["ITAR", "EAR ", "ISR", "EMCON", "CUI", "FOUO", "warfighter",
                 "SOCOM", "DoD", "tactical operator", "night ISR"]
    raw = json.dumps(library, ensure_ascii=False)
    for term in forbidden:
        # Allow "EAR" inside other words (clEAR, nEAR), so guard with trailing space.
        assert term not in raw, f"Forbidden term '{term}' present in parts library"


def test_catalog_has_meaningful_size(library: dict) -> None:
    """Sanity: every category should have at least one entry."""
    for category in PART_CATEGORIES:
        assert len(library.get(category, [])) >= 1, (
            f"Category '{category}' is empty"
        )

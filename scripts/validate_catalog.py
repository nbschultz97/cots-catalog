"""Catalog validation entrypoint for CI.

Exits non-zero if the bundled parts_library.json fails any validation:
JSON Schema, unique IDs, or required-field coverage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Make ``src/`` importable when running this script directly.
sys.path.insert(0, str(REPO_ROOT / "src"))

from architect_companion_mcp.validation import full_validation_report  # noqa: E402

LIB = REPO_ROOT / "data" / "parts_library.json"


def main() -> int:
    library = json.loads(LIB.read_text(encoding="utf-8"))
    report = full_validation_report(library)
    if report["ok"]:
        print("OK — parts library passes schema + uniqueness + required-field checks.")
        return 0

    print("FAIL — parts library validation issues:")
    for section, body in report.items():
        if section == "ok":
            continue
        if body.get("ok"):
            continue
        print(f"\n  [{section}]")
        for line in body.get("errors", []) or body.get("issues", []):
            print(f"    - {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

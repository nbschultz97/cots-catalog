"""Run compatibility checks against a hand-picked 5\" freestyle build.

Useful pattern: enumerate the IDs from `list_components`, then pass them
to `check_compatibility` to get a full pre-flight engineering report
(voltage chain, weight budget, mount patterns, KV vs prop, etc.).
"""

import json

from architect_companion_mcp.server import check_compatibility, get_part


def main() -> None:
    build = [
        "airframe-5in-true-x",
        "motor-iflight-xing2-2207-2050kv",
        "esc-diatone-mamba-f55-128k-4in1",
        "battery-tattu-rline-v5-4s-1300mah-150c",
        "fc-holybro-kakute-h7-v2",
        "radio-radiomaster-rp1-v2",
        "sensor-walksnail-avatar-hd-vtx-v2",
    ]

    print("Build manifest:")
    for pid in build:
        part = get_part(pid)
        print(f"  - {part['name']} ({part.get('weight_g', '?')}g, "
              f"${part.get('cost_usd', '?')})")
    print()

    report = check_compatibility(build)
    print(f"Compatible: {report['compatible']}")
    if report["issues"]:
        print("Issues:")
        for issue in report["issues"]:
            print(f"  - {issue}")
    if report.get("budget"):
        budget = report["budget"]
        print(f"\nWeight budget:")
        print(f"  airframe         : {budget['airframe_weight_g']}g")
        print(f"  components       : {budget['component_weight_g']}g")
        print(f"  payload limit    : {budget['max_payload_g']}g")
        print(f"  remaining        : {budget['remaining_budget_g']}g")


if __name__ == "__main__":
    main()

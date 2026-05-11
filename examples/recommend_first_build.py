"""Pick a first 5-inch freestyle kit for a beginner on a Pi 5.

Demonstrates the recommend_configuration tool plus the built-in
validation block that ships with v0.6.0.
"""

import json

from architect_companion_mcp.server import recommend_configuration


def main() -> None:
    rec = recommend_configuration(
        compute_tier="pi5",
        mission_type="long_range",
    )
    print(f"Suggested airframe : {rec['picks']['airframe']['name']}")
    print(f"Suggested motor    : {rec['picks']['motor']['name']}")
    print(f"Suggested battery  : {rec['picks']['battery']['name']}")
    print(f"Suggested ESC      : {rec['picks']['esc']['name']}")
    print(f"Suggested FC       : {rec['picks']['flight_controller']['name']}")
    print(f"Suggested RX       : {rec['picks']['control_radio']['name']}")
    print(f"Companion compute  : {rec['picks']['companion_compute']['name']} "
          f"({rec['picks']['companion_compute']['weight_g']}g)")
    print()
    print(f"Total parts cost   : ${rec['totals']['cost_usd']}")
    print(f"Total weight       : {rec['totals']['weight_g']}g "
          f"(compute {rec['totals']['compute_weight_g']}g)")
    print()
    print(f"Self-validation    : {'OK' if rec['validation']['compatible'] else 'ISSUES'}")
    for issue in rec["validation"]["issues"]:
        print(f"  - {issue}")
    if rec.get("warning"):
        print(f"\nWarning: {rec['warning']}")


if __name__ == "__main__":
    main()

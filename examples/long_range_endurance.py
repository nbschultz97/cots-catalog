"""Compare hover-endurance estimates across the four bundled airframes.

This is a sanity check, not a flight model — see the README's "Known
limitations" section. Cruise endurance on long-range and fixed-wing
platforms is typically 1.5-2x the hover number reported here.
"""

from architect_companion_mcp.server import estimate_flight_time, list_components


def main() -> None:
    airframes = list_components(category="airframes")
    batteries = list_components(category="batteries")

    print("Hover endurance approximations (200g payload, 14A draw, 20% reserve):\n")
    print(f"  {'Airframe':<55} {'Battery':<48} {'min':>5}")
    print("  " + "-" * 110)

    for af in airframes:
        # Pair each airframe with the heaviest in-stock battery for a rough max-endurance pick.
        best_battery = max(
            (b for b in batteries if b.get("availability") == "in-stock"),
            key=lambda b: (b.get("capacity_mah") or 0),
            default=None,
        )
        if not best_battery:
            continue
        result = estimate_flight_time(
            airframe_id=af["id"],
            battery_id=best_battery["id"],
            payload_weight_g=200,
            avg_current_draw_a=14,
        )
        print(
            f"  {af['name'][:54]:<55} "
            f"{best_battery['name'][:47]:<48} "
            f"{result['safe_endurance_min']:>5.1f}"
        )


if __name__ == "__main__":
    main()

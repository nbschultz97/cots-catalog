"""Seeder for v0.6.0 catalog additions.

Adds 8 manufacturer-sourced parts targeting beginner / tinywhoop /
sub-250g / HD-VTX builds so the catalog has coverage across all 7
bundled presets.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB = REPO_ROOT / "data" / "parts_library.json"
FETCHED_AT = "2026-05-11T08:00:00+00:00"


def ds(url: str, parser: str = "webfetch+manual") -> dict:
    return {"url": url, "fetched_at": FETCHED_AT, "parser": parser}


NEW_PARTS = {
    "airframes": [
        {
            "id": "airframe-betafpv-pavo20-pro",
            "name": "BetaFPV Pavo20 Pro Brushless Whoop Frame",
            "type": "multi-rotor",
            "weight_g": 33.3,
            "max_payload_g": 110,
            "dimensions_mm": {"length": 90, "width": 90, "height": 45},
            "motor_count": 4,
            "motor_size": "1404",
            "prop_size": "2x3",
            "material": "PA12",
            "printable": False,
            "manufacturer": "BetaFPV",
            "part_number": "BT-Pavo20-Pro-Frame",
            "cost_usd": 27.99,
            "availability": "in-stock",
            "notes": "2\" ducted cinewhoop frame for sub-150g HD builds. Compatible with DJI O3 / O4 Air Unit and Walksnail Avatar HD VTX.",
            "tags": ["multi-rotor", "2-inch", "cinewhoop", "tinywhoop", "ducted", "sub-250g"],
            "data_source": ds("https://betafpv.com/products/pavo20-pro-brushless-whoop-frame"),
        },
        {
            "id": "airframe-geprc-smart35-hd",
            "name": "GEPRC SMART 35 HD 3.5\" Micro Freestyle Frame",
            "type": "multi-rotor",
            "weight_g": 92,
            "max_payload_g": 250,
            "dimensions_mm": {"length": 156, "width": 156, "height": 40},
            "motor_count": 4,
            "motor_size": "1404",
            "prop_size": "3.5x2.8",
            "material": "carbon fiber",
            "printable": False,
            "manufacturer": "GEPRC",
            "part_number": "SMART-35-HD",
            "cost_usd": 95.00,
            "availability": "in-stock",
            "notes": "Sub-250g HD micro freestyle. 1404 motors at 3850KV. Compatible with Caddx Vista / Walksnail VTX.",
            "tags": ["multi-rotor", "3.5-inch", "cinematic", "sub-250g", "freestyle", "micro"],
            "data_source": ds("https://geprc.com/product/geprc-smart-35-hd-3-5inch-micro-freestyle-drone/"),
        },
    ],
    "motors": [
        {
            "id": "motor-happymodel-se0802-19000kv",
            "name": "Happymodel SE0802 19000KV Tinywhoop Motor",
            "size": "0802",
            "kv": 19000,
            "weight_g": 1.9,
            "max_current_a": 6,
            "max_power_w": 25,
            "max_thrust_g": 35,
            "voltage_range": {"min_v": 3.7, "max_v": 4.35},
            "prop_size_range": "31mm-40mm",
            "manufacturer": "Happymodel",
            "part_number": "SE0802-19000KV",
            "cost_usd": 9.99,
            "availability": "in-stock",
            "notes": "1S tinywhoop motor for Mobula6 / Mobula7 / 65-75mm whoops. 1.0mm shaft, 9N12P, JST1.25mm.",
            "tags": ["multi-rotor", "0802", "tinywhoop", "1s", "indoor", "brushless"],
            "data_source": ds("https://www.happymodel.cn/index.php/2018/08/30/happymodel-se0802-1-2s-16000kv-19000kv-brushless-motor-for-mobula6-7-rc-drone/"),
        },
    ],
    "escs": [
        {
            "id": "esc-diatone-mamba-f55-128k-4in1",
            "name": "Diatone Mamba F55 128K 55A 6S BLHeli_32 4-in-1 ESC",
            "max_current_a": 55,
            "weight_g": 14,
            "voltage_range": {"min_v": 12.6, "max_v": 25.2},
            "firmware": "BLHeli_32",
            "protocols": ["DShot300", "DShot600", "DShot1200", "PWM128K"],
            "integrated": True,
            "manufacturer": "Diatone",
            "part_number": "MB-F55_128K",
            "cost_usd": 49.99,
            "availability": "in-stock",
            "notes": "Premium 30.5x30.5mm 4-in-1 for 6S 5\" builds. 65A burst, metal EMI firewall, 470uF cap included.",
            "tags": ["esc", "4-in-1", "30x30", "blheli32", "6s", "55a"],
            "data_source": ds("https://www.diatone.us/products/mb-f55_128k-bl32-esc"),
        },
    ],
    "batteries": [
        {
            "id": "battery-tattu-rline-v5-4s-1300mah-150c",
            "name": "Tattu R-Line V5 4S 1300mAh 150C",
            "chemistry": "LiPo",
            "cells": 4,
            "voltage_nominal_v": 14.8,
            "capacity_mah": 1300,
            "capacity_wh": 19.24,
            "weight_g": 156,
            "c_rating": 150,
            "max_discharge_a": 195,
            "connector_type": "XT60",
            "dimensions_mm": {"length": 75, "width": 38, "height": 27},
            "manufacturer": "Tattu (Gens Ace)",
            "part_number": "TA-RL-V5-4S1300-150C",
            "cost_usd": 31.99,
            "availability": "in-stock",
            "notes": "Race-class 4S pack with Al Boehmite tech. 3-5\" FPV racing / freestyle.",
            "tags": ["4s", "1300mah", "race", "freestyle", "high-discharge"],
            "data_source": ds("https://genstattu.com/tattu-r-line-version-5-0-1300mah-4s-14-8v-150c-lipo-battery-pack-with-xt60-plug/"),
        },
    ],
    "radios": [
        {
            "id": "radio-radiomaster-pocket-elrs",
            "name": "RadioMaster Pocket ELRS 16ch Transmitter",
            "type": "control",
            "frequency_band": "2.4GHz",
            "frequency_range_mhz": {"min": 2400, "max": 2480},
            "weight_g": 288,
            "power_output_mw": 250,
            "power_levels_mw": [10, 25, 50, 100, 250],
            "data_rate_kbps": 1000,
            "protocols": ["ExpressLRS", "CRSF", "EdgeTX"],
            "voltage_input_v": {"min": 6.6, "max": 8.4},
            "manufacturer": "RadioMaster",
            "part_number": "HP0157-Pocket-ELRS-M2",
            "cost_usd": 89.00,
            "availability": "in-stock",
            "notes": "16-channel hall-gimbal ELRS pocket transmitter. EdgeTX, USB-C QC3 charging, dual 18650 (sold separately).",
            "tags": ["control", "transmitter", "elrs", "edgetx", "pocket", "2.4ghz"],
            "data_source": ds("https://radiomasterrc.com/products/pocket-radio-controller-m2"),
        },
    ],
    "sensors": [
        {
            "id": "sensor-walksnail-avatar-hd-vtx-v2",
            "name": "Walksnail Avatar HD VTX V2 (32GB)",
            "type": "camera",
            "weight_g": 17.6,
            "power_consumption_w": 7,
            "voltage_input_v": {"min": 6, "max": 25.2},
            "resolution": "1080p / 720p",
            "fov_degrees": 160,
            "interface": "Digital HD (5.8GHz)",
            "data_rate_mbps": 50,
            "manufacturer": "Walksnail (Caddx)",
            "part_number": "WS-AVATAR-HD-VTX-V2-32GB",
            "cost_usd": 169.99,
            "availability": "in-stock",
            "notes": "1080p HD digital FPV system. 22ms latency. 30.5x30.5 / 20x20 mount. 32GB onboard recording.",
            "tags": ["camera", "vtx", "hd", "walksnail", "5.8ghz", "digital", "recording"],
            "data_source": ds("https://www.caddxfpv.com/products/walksnail-avatar-hd-vtx-v2-only"),
        },
        {
            "id": "sensor-dji-o3-air-unit",
            "name": "DJI O3 Air Unit (Camera + VTX)",
            "type": "camera",
            "weight_g": 36.4,
            "power_consumption_w": 8,
            "voltage_input_v": {"min": 7.4, "max": 26.4},
            "resolution": "4K60 / 1080p120",
            "fov_degrees": 155,
            "interface": "Digital HD (5.8GHz)",
            "data_rate_mbps": 50,
            "manufacturer": "DJI",
            "part_number": "DJI-O3-AIR-UNIT",
            "cost_usd": 229.00,
            "availability": "in-stock",
            "notes": "32g VTX + camera combo. 30ms latency. 32.5x30.5x14.5mm module. 4K60 onboard recording.",
            "tags": ["camera", "vtx", "hd", "dji", "5.8ghz", "digital", "4k", "recording"],
            "data_source": ds("https://www.dji.com/o3-air-unit/specs"),
        },
    ],
}


def main() -> None:
    library = json.loads(LIB.read_text(encoding="utf-8"))

    added: list[tuple[str, str]] = []
    skipped: list[str] = []
    for category, entries in NEW_PARTS.items():
        existing_ids = {p["id"] for p in library.get(category, [])}
        for entry in entries:
            if entry["id"] in existing_ids:
                skipped.append(f"{category}/{entry['id']}")
                continue
            library.setdefault(category, []).append(entry)
            added.append((category, entry["id"]))

    library.setdefault("meta", {})["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    LIB.write_text(json.dumps(library, indent=2) + "\n", encoding="utf-8")
    print(f"Added {len(added)} parts:")
    for cat, pid in added:
        print(f"  {cat:25s} {pid}")
    if skipped:
        print(f"\nSkipped {len(skipped)} already-present IDs:")
        for s in skipped:
            print(f"  {s}")
    counts = {cat: len(library.get(cat, [])) for cat in NEW_PARTS}
    print(f"\nNew counts: {counts}")


if __name__ == "__main__":
    main()

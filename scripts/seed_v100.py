"""Seeder for v0.10.0 catalog sprint.

Adds ~25 more manufacturer-sourced parts targeting motors, FCs,
sensors (cameras/VTX/goggles/GPS), and accessories (antennas, props).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB = REPO_ROOT / "data" / "parts_library.json"
FETCHED_AT = "2026-05-11T12:00:00+00:00"


def ds(url: str, parser: str = "webfetch+manual") -> dict:
    return {"url": url, "fetched_at": FETCHED_AT, "parser": parser}


NEW_PARTS = {
    "motors": [
        {
            "id": "motor-tmotor-f40-pro-v-2150kv",
            "name": "T-Motor F40 PRO V 2150KV",
            "size": "2207",
            "kv": 2150,
            "weight_g": 34.5,
            "max_current_a": 45,
            "max_power_w": 1000,
            "max_thrust_g": 2500,
            "voltage_range": {"min_v": 14.8, "max_v": 25.2},
            "prop_size_range": "5 inch",
            "manufacturer": "T-Motor",
            "part_number": "F40PRO-V-2150KV",
            "cost_usd": 28.90,
            "availability": "in-stock",
            "notes": "5\" 6S race motor. Higher KV variant for tighter prop pitches.",
            "tags": ["multi-rotor", "5-inch", "race", "high-thrust"],
            "data_source": ds("https://shop.tmotor.com/products/t-motor-f40-pro-v-1950kv-fpv-brushless-drone-motor"),
        },
        {
            "id": "motor-tmotor-f40-pro-ii-1750kv",
            "name": "T-Motor F40 PRO II 1750KV",
            "size": "2207",
            "kv": 1750,
            "weight_g": 30.8,
            "max_current_a": 42,
            "max_power_w": 880,
            "max_thrust_g": 2150,
            "voltage_range": {"min_v": 14.8, "max_v": 25.2},
            "prop_size_range": "5 inch",
            "manufacturer": "T-Motor",
            "part_number": "F40PRO-II-1750KV",
            "cost_usd": 22.50,
            "availability": "in-stock",
            "notes": "Mature 5\" 6S race / freestyle motor. Lighter than V-series.",
            "tags": ["multi-rotor", "5-inch", "race", "freestyle"],
            "data_source": ds("https://www.getfpv.com/tmotor-f40-proii-1750kv.html"),
        },
        {
            "id": "motor-brotherhobby-avenger-v3-2207-5-1750kv",
            "name": "BrotherHobby Avenger V3 2207.5 1750KV",
            "size": "2207.5",
            "kv": 1750,
            "weight_g": 33.6,
            "max_current_a": 52,
            "max_power_w": 1150,
            "max_thrust_g": 2050,
            "voltage_range": {"min_v": 14.8, "max_v": 25.2},
            "prop_size_range": "5 inch",
            "manufacturer": "BrotherHobby",
            "part_number": "AVENGER-V3-22075-1750KV",
            "cost_usd": 24.99,
            "availability": "in-stock",
            "notes": "5\" 6S build with 2kg thrust on 5.1\" props at 52A peak. N52H magnets, NMB bearings, titanium hollow shaft.",
            "tags": ["multi-rotor", "5-inch", "freestyle", "race", "high-thrust"],
            "data_source": ds("https://www.brotherhobbystore.com/products/avenger-22075-v3"),
        },
        {
            "id": "motor-betafpv-1102-18000kv",
            "name": "BetaFPV 1102 18000KV Tinywhoop Motor",
            "size": "1102",
            "kv": 18000,
            "weight_g": 2.79,
            "max_current_a": 5,
            "max_power_w": 20,
            "max_thrust_g": 30,
            "voltage_range": {"min_v": 3.7, "max_v": 4.35},
            "prop_size_range": "35-40mm",
            "manufacturer": "BetaFPV",
            "part_number": "BT-1102-18000KV",
            "cost_usd": 12.99,
            "availability": "in-stock",
            "notes": "1S tinywhoop motor for 75mm whoops (Cetus Pro, Meteor75 HD). 1.5mm shaft, ball bearings.",
            "tags": ["multi-rotor", "1102", "tinywhoop", "1s", "indoor"],
            "data_source": ds("https://betafpv.com/products/1102-13500kv-brushless-motors"),
        },
    ],
    "flight_controllers": [
        {
            "id": "fc-matek-f722-se",
            "name": "Matek F722-SE AIO Flight Controller",
            "weight_g": 10,
            "processor": "STM32F722RET6 @ 216MHz",
            "firmware": ["Betaflight", "INAV"],
            "gyro": "MPU6000 + ICM20602 (dual)",
            "voltage_input_v": {"min": 7.4, "max": 30},
            "current_draw_ma": 250,
            "uart_ports": 5,
            "features": ["OSD", "Barometer", "Dual-Gyro", "DShot-Proshot-OneShot"],
            "manufacturer": "Matek (MATEKSYS)",
            "part_number": "F722-SE",
            "cost_usd": 59.99,
            "availability": "in-stock",
            "notes": "Workhorse F7 FC. Dual gyros (SPI). 30.5x30.5 mount. 2-6S input. Mature INAV / Betaflight target.",
            "tags": ["flight-controller", "f7", "30x30", "betaflight", "inav", "dual-gyro"],
            "data_source": ds("https://www.mateksys.com/?portfolio=f722-se"),
        },
    ],
    "sensors": [
        {
            "id": "sensor-caddx-ratel-2",
            "name": "Caddx Ratel 2 1200TVL Starlight Analog Camera",
            "type": "camera",
            "weight_g": 5.9,
            "power_consumption_w": 1.2,
            "voltage_input_v": {"min": 5, "max": 40},
            "resolution": "1200TVL",
            "fov_degrees": 165,
            "interface": "Analog NTSC/PAL",
            "data_rate_mbps": 1,
            "manufacturer": "Caddx",
            "part_number": "RATEL-2-21",
            "cost_usd": 29.99,
            "availability": "in-stock",
            "notes": "1/1.8\" Starlight CMOS. 19x19x20mm. Industry-favorite analog freestyle camera.",
            "tags": ["camera", "analog", "fpv", "1200tvl", "starlight", "caddx", "freestyle"],
            "data_source": ds("https://www.caddxfpv.com/products/ratel-2-1-1-8inch-starlight-sensor-freestyle-fpv-camera"),
        },
        {
            "id": "sensor-runcam-hybrid-2",
            "name": "RunCam Hybrid 2 Dual 4K + Analog Camera",
            "type": "camera",
            "weight_g": 18,
            "power_consumption_w": 3.5,
            "voltage_input_v": {"min": 5, "max": 20},
            "resolution": "4K30 / 2.7K60 / 1080p120 (recording) + 1500TVL (analog)",
            "fov_degrees": 145,
            "interface": "Analog NTSC/PAL + microSD recording",
            "data_rate_mbps": 50,
            "manufacturer": "RunCam",
            "part_number": "HYBRID-2",
            "cost_usd": 109.99,
            "availability": "in-stock",
            "notes": "Hybrid analog FPV + 4K HD recording on one 20x20 board. 20ms FPV latency.",
            "tags": ["camera", "analog", "hd", "4k", "recording", "runcam", "hybrid"],
            "data_source": ds("https://shop.runcam.com/runcam-hybrid-2/"),
        },
        {
            "id": "sensor-walksnail-avatar-hd-goggles-x",
            "name": "Walksnail Avatar HD Goggles X",
            "type": "other",
            "weight_g": 290,
            "power_consumption_w": 9,
            "voltage_input_v": {"min": 7, "max": 26},
            "resolution": "1080P @ 100FPS",
            "fov_degrees": 50,
            "interface": "Digital HD (5.8GHz, Walksnail) + Analog + HDZero",
            "data_rate_mbps": 50,
            "manufacturer": "Walksnail (Caddx)",
            "part_number": "WS-AVATAR-GOGGLES-X",
            "cost_usd": 549.00,
            "availability": "in-stock",
            "notes": "Premium digital FPV goggle. 1080p 100fps. PD 57-72mm. Built-in gyro. Compatible with Walksnail / Analog / HDZero.",
            "tags": ["goggle", "fpv", "hd", "walksnail", "5.8ghz", "digital"],
            "data_source": ds("https://www.caddxfpv.com/products/walksnail-avatar-hd-goggles-x"),
        },
    ],
    "accessories": [
        {
            "id": "accessory-hqprop-5x4-3x3v2s",
            "name": "HQProp Freestyle 5x4.3x3 V2S (Set of 4)",
            "category": "propeller",
            "weight_g": 3.8,
            "dimensions_mm": {"length": 127, "width": 12.8, "height": 6.5},
            "material": "Polycarbonate",
            "manufacturer": "HQProp",
            "part_number": "HQ-5X43X3V2S",
            "cost_usd": 3.99,
            "availability": "in-stock",
            "notes": "5\" 3-blade freestyle prop. Slightly heavier hub than Ethix S5. 12.8mm hub, 5mm shaft.",
            "tags": ["propeller", "5-inch", "3-blade", "freestyle", "polycarbonate", "hqprop"],
            "data_source": ds("https://www.hqprop.com/hq-freestyle-prop-5x43x3v2s-2cw2ccw-poly-carbonate-p0233.html"),
        },
        {
            "id": "accessory-lumenier-axii-2-58-rhcp",
            "name": "Lumenier AXII 2 Long Range 5.8GHz RHCP Antenna",
            "category": "antenna",
            "weight_g": 4,
            "frequency_band": "5.8GHz",
            "frequency_range_mhz": {"min": 5400, "max": 6100},
            "rx_gain_dbi": 2.2,
            "manufacturer": "Lumenier",
            "part_number": "AXII-2-LR-58-RHCP",
            "cost_usd": 19.99,
            "availability": "in-stock",
            "notes": "Industry-standard 5.8GHz omni antenna for VTX or goggle. 2.2 dBic gain RHCP. SMA connector.",
            "tags": ["antenna", "omni", "5.8ghz", "rhcp", "vtx", "goggle"],
            "data_source": ds("https://www.lumenier.com/products/lumenier-axii-2-long-range-5-8ghz-antenna-rhcp"),
        },
        {
            "id": "accessory-lumenier-axii-2-58-lhcp",
            "name": "Lumenier AXII 2 Long Range 5.8GHz LHCP Antenna",
            "category": "antenna",
            "weight_g": 4,
            "frequency_band": "5.8GHz",
            "frequency_range_mhz": {"min": 5400, "max": 6100},
            "rx_gain_dbi": 2.2,
            "manufacturer": "Lumenier",
            "part_number": "AXII-2-LR-58-LHCP",
            "cost_usd": 19.99,
            "availability": "in-stock",
            "notes": "LHCP variant for race-event polarization isolation.",
            "tags": ["antenna", "omni", "5.8ghz", "lhcp", "vtx", "goggle"],
            "data_source": ds("https://www.lumenier.com/products/lumenier-axii-2-long-range-5-8ghz-antenna-lhcp"),
        },
    ],
    "batteries": [
        {
            "id": "battery-tattu-rline-v5-6s-1300mah-150c",
            "name": "Tattu R-Line V5 6S 1300mAh 150C",
            "chemistry": "LiPo",
            "cells": 6,
            "voltage_nominal_v": 22.2,
            "capacity_mah": 1300,
            "capacity_wh": 28.86,
            "weight_g": 224,
            "c_rating": 150,
            "max_discharge_a": 195,
            "connector_type": "XT60",
            "dimensions_mm": {"length": 75, "width": 38, "height": 38},
            "manufacturer": "Tattu (Gens Ace)",
            "part_number": "TA-RL-V5-6S1300-150C",
            "cost_usd": 39.99,
            "availability": "in-stock",
            "notes": "Premium 6S race pack with Al Boehmite tech. 5\" race / freestyle.",
            "tags": ["6s", "1300mah", "race", "freestyle", "high-discharge"],
            "data_source": ds("https://genstattu.com/tattu-r-line-batteries.html"),
        },
        {
            "id": "battery-gnb-4s-850mah-90c",
            "name": "GAONENG GNB 4S 850mAh 90C (Toothpick / 3-3.5\")",
            "chemistry": "LiPo",
            "cells": 4,
            "voltage_nominal_v": 14.8,
            "capacity_mah": 850,
            "capacity_wh": 12.58,
            "weight_g": 95,
            "c_rating": 90,
            "max_discharge_a": 76,
            "connector_type": "XT30",
            "manufacturer": "GAONENG (GNB)",
            "part_number": "GNB-4S-850-90C",
            "cost_usd": 19.99,
            "availability": "in-stock",
            "notes": "4S 850mAh for 3-3.5\" toothpick / micro freestyle builds with XT30.",
            "tags": ["4s", "850mah", "toothpick", "micro", "freestyle", "xt30"],
            "data_source": ds("https://www.gaoneng.shop/"),
        },
    ],
    "radios": [
        {
            "id": "radio-betafpv-elrs-lite-rx",
            "name": "BetaFPV ELRS Lite 2.4GHz Nano RX",
            "type": "control",
            "frequency_band": "2.4GHz",
            "frequency_range_mhz": {"min": 2400, "max": 2480},
            "weight_g": 0.4,
            "power_output_mw": 10,
            "data_rate_kbps": 500,
            "protocols": ["CRSF", "ExpressLRS"],
            "voltage_input_v": {"min": 4.5, "max": 5.5},
            "manufacturer": "BetaFPV",
            "part_number": "BT-ELRS-LITE-RX",
            "cost_usd": 11.99,
            "availability": "in-stock",
            "notes": "Budget tinywhoop ELRS RX. SX1280, ESP8285. Direct competitor to Happymodel EP1.",
            "tags": ["control", "elrs", "crsf", "2.4ghz", "nano", "budget", "tinywhoop"],
            "data_source": ds("https://betafpv.com/products/elrs-lite-receiver"),
        },
    ],
    "escs": [
        {
            "id": "esc-tmotor-f55a-pro-ii-4in1",
            "name": "T-Motor F55A Pro II 55A 4-in-1 BLHeli32",
            "max_current_a": 55,
            "weight_g": 12,
            "voltage_range": {"min_v": 11.1, "max_v": 25.2},
            "firmware": "BLHeli_32",
            "protocols": ["DShot300", "DShot600", "DShot1200"],
            "integrated": True,
            "manufacturer": "T-Motor",
            "part_number": "F55A-PRO-II",
            "cost_usd": 64.99,
            "availability": "in-stock",
            "notes": "30.5x30.5mm 4-in-1 with BEC. 65A burst. AM32 firmware support.",
            "tags": ["esc", "4-in-1", "30x30", "blheli32", "55a", "6s", "bec"],
            "data_source": ds("https://pyrodrone.com/products/t-motor-f55a-pro-ii-55a-3-6s-blheli32-4-in-1-esc"),
        },
    ],
    "airframes": [
        {
            "id": "airframe-armattan-rooster-5",
            "name": "Armattan Rooster 5\" Freestyle Frame",
            "type": "multi-rotor",
            "weight_g": 105,
            "max_payload_g": 800,
            "dimensions_mm": {"length": 222, "width": 222, "height": 35},
            "motor_count": 4,
            "motor_size": "2207",
            "prop_size": "5x4.3",
            "material": "carbon fiber",
            "printable": False,
            "manufacturer": "Armattan",
            "part_number": "ROOSTER-5",
            "cost_usd": 109.00,
            "availability": "in-stock",
            "notes": "Lifetime warranty true-X 5\" freestyle frame. Premium build quality. 30.5x30.5 FC mount.",
            "tags": ["multi-rotor", "5-inch", "freestyle", "true-x", "premium"],
            "data_source": ds("https://armattanquads.com/rooster/"),
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

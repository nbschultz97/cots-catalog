"""One-shot seeder that adds ingested manufacturer parts to parts_library.json.

Each new part has a ``data_source`` block (url + fetched_at + parser) so
the catalog provenance is auditable.

Run from repo root: ``python scripts/seed_v050.py``
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB = REPO_ROOT / "data" / "parts_library.json"
FETCHED_AT = "2026-05-11T06:30:00+00:00"


def ds(url: str, parser: str = "webfetch+manual") -> dict:
    return {"url": url, "fetched_at": FETCHED_AT, "parser": parser}


NEW_PARTS = {
    "motors": [
        {
            "id": "motor-iflight-xing2-2207-1750kv",
            "name": "iFlight XING2 2207 1750KV Unibell",
            "size": "2207",
            "kv": 1750,
            "weight_g": 30.5,
            "max_current_a": 36.03,
            "max_power_w": 720,
            "max_thrust_g": 2100,
            "voltage_range": {"min_v": 16.8, "max_v": 25.2},
            "prop_size_range": "5 inch",
            "manufacturer": "iFlight",
            "part_number": "XING2-2207-1750KV-UNI",
            "cost_usd": 23.99,
            "availability": "in-stock",
            "notes": "5\" 4S-6S workhorse. Center slotted N52H magnets, 5mm titanium shaft, 16x16 mount.",
            "tags": ["multi-rotor", "5-inch", "freestyle", "long-range-5in"],
            "data_source": ds("https://shop.iflight.com/XING2-2207-4S-6S-FPV-Motor-Unibell-Black-for-Nazgul-Evoque-F5-pro1610"),
        },
        {
            "id": "motor-iflight-xing2-2207-2050kv",
            "name": "iFlight XING2 2207 2050KV Unibell",
            "size": "2207",
            "kv": 2050,
            "weight_g": 30.5,
            "max_current_a": 49.53,
            "max_power_w": 880,
            "max_thrust_g": 2200,
            "voltage_range": {"min_v": 14.8, "max_v": 22.2},
            "prop_size_range": "5 inch",
            "manufacturer": "iFlight",
            "part_number": "XING2-2207-2050KV-UNI",
            "cost_usd": 23.99,
            "availability": "in-stock",
            "notes": "5\" freestyle / race. Same 30.5g body; 49A peak draw matches Lumenier 51A ESC.",
            "tags": ["multi-rotor", "5-inch", "race", "freestyle"],
            "data_source": ds("https://shop.iflight.com/XING2-2207-4S-6S-FPV-Motor-Unibell-Black-for-Nazgul-Evoque-F5-pro1610"),
        },
        {
            "id": "motor-emax-eco-ii-2207-2400kv",
            "name": "EMAX ECO II 2207 2400KV",
            "size": "2207",
            "kv": 2400,
            "weight_g": 32,
            "max_current_a": 36,
            "max_power_w": 770,
            "max_thrust_g": 2050,
            "voltage_range": {"min_v": 11.1, "max_v": 22.2},
            "prop_size_range": "5 inch",
            "manufacturer": "EMAX",
            "part_number": "ECO222072400",
            "cost_usd": 12.99,
            "availability": "in-stock",
            "notes": "Budget 5\" race motor. N52SH arc magnets, 16x16 mount, EZO 9mm bearings.",
            "tags": ["multi-rotor", "5-inch", "race", "budget"],
            "data_source": ds("https://emax-usa.com/products/eco-ii-2207-brushless-motor-1700kv-1900kv-2400kv"),
        },
        {
            "id": "motor-tmotor-f40-pro-v-1950kv",
            "name": "T-Motor F40 PRO V 1950KV",
            "size": "2207",
            "kv": 1950,
            "weight_g": 32.5,
            "max_current_a": 41.5,
            "max_power_w": 920,
            "max_thrust_g": 2300,
            "voltage_range": {"min_v": 14.8, "max_v": 25.2},
            "prop_size_range": "5 inch",
            "manufacturer": "T-Motor",
            "part_number": "F40PRO-V-1950KV",
            "cost_usd": 26.90,
            "availability": "in-stock",
            "notes": "5\" 6S race / high-thrust freestyle. EZO bearings, hollow shaft.",
            "tags": ["multi-rotor", "5-inch", "race", "high-thrust"],
            "data_source": ds("https://store.tmotor.com/product/f40pro-5-fpv-motor.html"),
        },
    ],
    "radios": [
        {
            "id": "radio-radiomaster-rp1-v2",
            "name": "RadioMaster RP1 V2 ExpressLRS 2.4GHz Nano RX",
            "type": "control",
            "frequency_band": "2.4GHz",
            "frequency_range_mhz": {"min": 2404, "max": 2479},
            "weight_g": 2.2,
            "power_output_mw": 10,
            "rx_sensitivity_dbm": -108,
            "power_consumption_w": 0.1,
            "data_rate_kbps": 1000,
            "antenna_connector": "U.FL",
            "protocols": ["CRSF", "ExpressLRS"],
            "voltage_input_v": {"min": 4.5, "max": 5.5},
            "manufacturer": "RadioMaster",
            "part_number": "HP0157.RX-RP1-V2",
            "cost_usd": 18.99,
            "availability": "in-stock",
            "notes": "TCXO-stabilized ELRS nano RX. SX1281 RF chip, ESP8285 MCU. 65mm T-antenna in box.",
            "tags": ["control", "elrs", "crsf", "2.4ghz", "nano"],
            "data_source": ds("https://radiomasterrc.com/products/rp1-expresslrs-2-4ghz-nano-receiver", "jsonld"),
        },
        {
            "id": "radio-radiomaster-xr1-nano-db",
            "name": "RadioMaster XR1 Nano Dual-Band ExpressLRS RX",
            "type": "control",
            "frequency_band": "Dual-band",
            "frequency_range_mhz": {"min": 868, "max": 2479},
            "weight_g": 1.0,
            "power_output_mw": 100,
            "data_rate_kbps": 1000,
            "antenna_connector": "IPEX-1",
            "protocols": ["CRSF", "ExpressLRS"],
            "voltage_input_v": {"min": 4.5, "max": 5.5},
            "manufacturer": "RadioMaster",
            "part_number": "HP0157.XR1-DB",
            "cost_usd": 11.99,
            "availability": "in-stock",
            "notes": "Dual-band 2.4GHz + 900MHz ELRS RX. Semtech LR1121 RF, ESP32C3 MCU. 1g (no antenna).",
            "tags": ["control", "elrs", "crsf", "dual-band", "nano"],
            "data_source": ds("https://radiomasterrc.com/products/xr1-nano-multi-frequency-expresslrs-receiver"),
        },
        {
            "id": "radio-radiomaster-er6-pwm",
            "name": "RadioMaster ER6 2.4GHz ELRS PWM RX",
            "type": "control",
            "frequency_band": "2.4GHz",
            "frequency_range_mhz": {"min": 2404, "max": 2479},
            "weight_g": 14.5,
            "power_output_mw": 100,
            "protocols": ["CRSF", "SBUS", "PWM", "ExpressLRS"],
            "voltage_input_v": {"min": 4.5, "max": 8.4},
            "manufacturer": "RadioMaster",
            "part_number": "HP0157.RX-ER6",
            "cost_usd": 24.99,
            "availability": "in-stock",
            "notes": "6-channel PWM ELRS RX for fixed-wing / non-FC builds. Dual-antenna.",
            "tags": ["control", "elrs", "pwm", "sbus", "fixed-wing"],
            "data_source": ds("https://radiomasterrc.com/products/er6-2-4ghz-elrs-pwm-receiver"),
        },
    ],
    "flight_controllers": [
        {
            "id": "fc-holybro-kakute-h7-v2",
            "name": "Holybro Kakute H7 V2 Flight Controller",
            "weight_g": 11,
            "processor": "STM32H743 @ 480MHz",
            "firmware": ["Betaflight", "INAV", "ArduPilot", "PX4"],
            "gyro": "BMI270",
            "voltage_input_v": {"min": 7.4, "max": 33.6},
            "current_draw_ma": 250,
            "uart_ports": 6,
            "features": ["OSD", "Bluetooth", "Barometer", "Logging128MB", "9V-BEC", "5V-BEC"],
            "manufacturer": "Holybro",
            "part_number": "KAKUTE-H7-V2",
            "cost_usd": 89.99,
            "availability": "in-stock",
            "notes": "30.5x30.5 mount. 2S-8S input. ESP32-C3 onboard Bluetooth. 9V VTX pit switch.",
            "tags": ["flight-controller", "h7", "30x30", "betaflight", "ardupilot", "bluetooth"],
            "data_source": ds("https://holybro.com/products/kakute-h7-v2"),
        },
    ],
    "batteries": [
        {
            "id": "battery-gnb-6s-1300mah-120c",
            "name": "GAONENG GNB 6S 1300mAh 120C (5\" race / freestyle)",
            "chemistry": "LiPo",
            "cells": 6,
            "voltage_nominal_v": 22.2,
            "capacity_mah": 1300,
            "capacity_wh": 28.86,
            "weight_g": 226,
            "c_rating": 120,
            "max_discharge_a": 156,
            "connector_type": "XT60",
            "dimensions_mm": {"length": 76, "width": 35, "height": 46},
            "manufacturer": "GAONENG (GNB)",
            "part_number": "GNB-6S-1300-120C",
            "cost_usd": 38.99,
            "availability": "in-stock",
            "notes": "Green-label race pack. 240C burst. Fits standard 5\" freestyle bays.",
            "tags": ["6s", "1300mah", "race", "freestyle", "high-discharge"],
            "data_source": ds("https://www.gaoneng.shop/products/gaoneng-gnb-lihv-6s-22.8v-1300mah-120c-xt60-lipo-battery"),
        },
        {
            "id": "battery-cnhl-black-6s-1300mah-130c",
            "name": "CNHL Black Series V2 6S 1300mAh 130C",
            "chemistry": "LiPo",
            "cells": 6,
            "voltage_nominal_v": 22.2,
            "capacity_mah": 1300,
            "capacity_wh": 28.86,
            "weight_g": 220,
            "c_rating": 130,
            "max_discharge_a": 169,
            "connector_type": "XT60",
            "manufacturer": "CNHL",
            "part_number": "CNHL-BLK-V2-6S-1300",
            "cost_usd": 32.99,
            "availability": "in-stock",
            "notes": "Black Series — premium race pack with low internal resistance. Common alternative to GNB.",
            "tags": ["6s", "1300mah", "race", "freestyle", "high-discharge"],
            "data_source": ds("https://www.getfpv.com/cnhl-black-series-v2-0-1300mah-22-2v-130c-6s-lipo-battery-xt60.html"),
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

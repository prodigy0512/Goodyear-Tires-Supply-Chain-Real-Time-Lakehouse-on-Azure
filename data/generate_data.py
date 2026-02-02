"""
Synthetic data generator for the Goodyear supply chain project.

It creates:
- plants, products
- inventory snapshots
- production orders
- purchase orders + suppliers
- shipments + streaming shipment events
- simple IoT telemetry (press temperature/vibration)

Run:
  python generate_data.py --out sample_out --days 30 --plants 3
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

RNG = random.Random(42)

PRODUCTS = [
    ("TIR-001", "All-Season 205/55R16", "Passenger"),
    ("TIR-002", "Winter 195/65R15", "Passenger"),
    ("TIR-003", "Performance 225/40R18", "Passenger"),
    ("TIR-101", "Truck A/T 265/70R17", "LightTruck"),
    ("TIR-201", "OTR 14.00R25", "Industrial"),
]

SUPPLIERS = [
    ("SUP-001", "RubberCo", "US"),
    ("SUP-002", "ChemMix Ltd", "CA"),
    ("SUP-003", "SteelCord Inc", "MX"),
    ("SUP-004", "CarbonBlack AG", "DE"),
    ("SUP-005", "SyntheticPolymers", "JP"),
]

CARRIERS = ["DHL", "FedEx", "XPO", "UPS", "Maersk"]


def iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def gen_plants(n: int):
    plants = []
    for i in range(1, n + 1):
        plants.append({
            "plant_id": f"PLT-{i:03d}",
            "plant_name": f"Plant {i}",
            "region": RNG.choice(["NE", "SE", "MW", "SW", "W"]),
            "timezone": "America/New_York",
        })
    return plants


def gen_inventory(plants, start: datetime, days: int):
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        for p in plants:
            for sku, _, _ in PRODUCTS:
                # base inventory varies by SKU family
                base = 800 if sku.startswith("TIR-0") else 200
                noise = int(RNG.gauss(0, base * 0.08))
                qty = max(0, base + noise - int(d * RNG.random() * 5))
                rows.append({
                    "snapshot_date": day.date().isoformat(),
                    "plant_id": p["plant_id"],
                    "sku": sku,
                    "on_hand_qty": qty,
                    "safety_stock_qty": int(base * 0.35),
                })
    return rows


def gen_production_orders(plants, start: datetime, days: int):
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        for p in plants:
            # 5–15 orders per day per plant
            for _ in range(RNG.randint(5, 15)):
                sku, _, _ = RNG.choice(PRODUCTS)
                qty = RNG.randint(200, 1200) if sku.startswith("TIR-0") else RNG.randint(20, 150)
                cycle_min = RNG.uniform(0.8, 2.2) if sku.startswith("TIR-0") else RNG.uniform(5.0, 12.0)
                start_ts = day + timedelta(minutes=RNG.randint(0, 1439))
                end_ts = start_ts + timedelta(minutes=math.ceil(qty * cycle_min))
                rows.append({
                    "prod_order_id": f"PO-{p['plant_id']}-{day:%Y%m%d}-{RNG.randint(1000,9999)}",
                    "plant_id": p["plant_id"],
                    "sku": sku,
                    "planned_qty": qty,
                    "actual_qty": max(0, int(qty * RNG.uniform(0.92, 1.03))),
                    "start_ts": iso(start_ts),
                    "end_ts": iso(end_ts),
                    "scrap_qty": max(0, int(qty * RNG.uniform(0.0, 0.03))),
                })
    return rows


def gen_purchase_orders(start: datetime, days: int):
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        # 10–25 POs/day
        for _ in range(RNG.randint(10, 25)):
            sup_id, sup_name, sup_country = RNG.choice(SUPPLIERS)
            sku, _, _ = RNG.choice(PRODUCTS)
            qty = RNG.randint(500, 5000) if sku.startswith("TIR-0") else RNG.randint(50, 400)
            lead = RNG.randint(3, 21)
            rows.append({
                "cloud_po_id": f"CPO-{day:%Y%m%d}-{RNG.randint(100000,999999)}",
                "supplier_id": sup_id,
                "supplier_name": sup_name,
                "supplier_country": sup_country,
                "sku": sku,
                "order_qty": qty,
                "order_date": day.date().isoformat(),
                "expected_delivery_date": (day + timedelta(days=lead)).date().isoformat(),
                "unit_cost_usd": round(RNG.uniform(40, 220), 2),
                "status": RNG.choice(["OPEN", "OPEN", "OPEN", "CLOSED", "CANCELLED"]),
            })
    return rows


def gen_shipments(plants, start: datetime, days: int):
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        # 6–18 shipments/day across network
        for _ in range(RNG.randint(6, 18)):
            p = RNG.choice(plants)
            carrier = RNG.choice(CARRIERS)
            sku, _, _ = RNG.choice(PRODUCTS)
            qty = RNG.randint(100, 2000) if sku.startswith("TIR-0") else RNG.randint(10, 120)
            ship_ts = day + timedelta(minutes=RNG.randint(0, 1439))
            eta = ship_ts + timedelta(hours=RNG.randint(6, 72))
            rows.append({
                "shipment_id": f"SHP-{day:%Y%m%d}-{RNG.randint(10000,99999)}",
                "plant_id": p["plant_id"],
                "carrier": carrier,
                "sku": sku,
                "shipped_qty": qty,
                "ship_ts": iso(ship_ts),
                "eta_ts": iso(eta),
                "status": RNG.choice(["CREATED", "IN_TRANSIT", "IN_TRANSIT", "DELIVERED", "DELAYED"]),
                "destination_dc": f"DC-{RNG.randint(1,9):03d}",
            })
    return rows


def gen_shipment_events(shipments):
    # create a few events per shipment, with late arrivals
    events = []
    for s in shipments:
        ship_ts = datetime.fromisoformat(s["ship_ts"].replace("Z", "+00:00"))
        eta_ts = datetime.fromisoformat(s["eta_ts"].replace("Z", "+00:00"))
        current = ship_ts
        # 3–8 events
        for i in range(RNG.randint(3, 8)):
            current = current + timedelta(hours=RNG.randint(1, 10))
            status = RNG.choice(["IN_TRANSIT", "IN_TRANSIT", "AT_HUB", "DELAYED", "OUT_FOR_DELIVERY"])
            # final event
            if current > eta_ts and RNG.random() < 0.6:
                status = "DELAYED"
            if i == 7 or (eta_ts - current).total_seconds() < 3600 and RNG.random() < 0.7:
                status = "DELIVERED"
                current = max(current, eta_ts + timedelta(hours=RNG.randint(-2, 18)))
            events.append({
                "event_id": f"EVT-{s['shipment_id']}-{i}",
                "shipment_id": s["shipment_id"],
                "event_ts": iso(current),
                "status": status,
                "lat": round(RNG.uniform(25.0, 49.0), 5),
                "lon": round(RNG.uniform(-124.0, -67.0), 5),
            })
            if status == "DELIVERED":
                break
    return events


def gen_iot(plants, start: datetime, days: int):
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        for p in plants:
            for press in range(1, 6):  # 5 presses per plant
                for _ in range(24):  # hourly readings
                    ts = day + timedelta(hours=_)
                    base_temp = 85 + RNG.uniform(-3, 3)
                    vib = RNG.uniform(0.1, 0.9)
                    # occasional anomaly
                    if RNG.random() < 0.02:
                        base_temp += RNG.uniform(10, 25)
                        vib += RNG.uniform(1.0, 2.2)
                    rows.append({
                        "ts": iso(ts),
                        "plant_id": p["plant_id"],
                        "press_id": f"{p['plant_id']}-PRS-{press:02d}",
                        "temperature_c": round(base_temp, 2),
                        "vibration_mm_s": round(vib, 3),
                    })
    return rows


def write_csv(path: Path, rows, fieldnames):
    mkdir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path: Path, rows):
    mkdir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output folder")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--plants", type=int, default=3)
    ap.add_argument("--start", default=None, help="Start date YYYY-MM-DD (default: today-<days>)")
    args = ap.parse_args()

    out = Path(args.out)
    mkdir(out)

    end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = datetime.fromisoformat(args.start) if args.start else end - timedelta(days=args.days)

    plants = gen_plants(args.plants)
    inventory = gen_inventory(plants, start, args.days)
    prod = gen_production_orders(plants, start, args.days)
    cpo = gen_purchase_orders(start, args.days)
    shipments = gen_shipments(plants, start, args.days)
    events = gen_shipment_events(shipments)
    iot = gen_iot(plants, start, args.days)

    # Write
    write_csv(out / "master" / "plants.csv", plants, ["plant_id", "plant_name", "region", "timezone"])
    write_csv(out / "master" / "products.csv", [
        {"sku": sku, "product_name": name, "category": cat} for sku, name, cat in PRODUCTS
    ], ["sku", "product_name", "category"])
    write_csv(out / "erp" / "inventory_snapshot.csv", inventory,
              ["snapshot_date", "plant_id", "sku", "on_hand_qty", "safety_stock_qty"])
    write_csv(out / "erp" / "production_orders.csv", prod,
              ["prod_order_id", "plant_id", "sku", "planned_qty", "actual_qty", "start_ts", "end_ts", "scrap_qty"])
    write_csv(out / "oracle_cloud" / "purchase_orders.csv", cpo,
              ["cloud_po_id", "supplier_id", "supplier_name", "supplier_country", "sku",
               "order_qty", "order_date", "expected_delivery_date", "unit_cost_usd", "status"])
    write_csv(out / "logistics" / "shipments.csv", shipments,
              ["shipment_id", "plant_id", "carrier", "sku", "shipped_qty", "ship_ts", "eta_ts", "status", "destination_dc"])
    write_jsonl(out / "stream" / "shipment_events.jsonl", events)
    write_csv(out / "iot" / "press_telemetry.csv", iot,
              ["ts", "plant_id", "press_id", "temperature_c", "vibration_mm_s"])

    print(f"✅ Generated data in: {out.resolve()}")

if __name__ == "__main__":
    main()

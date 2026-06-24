"""Generate messy mock fleet dataset -> data/raw/fleet_raw.csv"""
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

N = 5200
RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "fleet_raw.csv"

LOCATIONS = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "n/a", "", "UNKNOWN"]
VEHICLE_IDS = [f"VEH-{i:04d}" for i in range(1, 251)]
DRIVER_IDS = [f"DRV-{i:04d}" for i in range(1, 401)]

TS_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%m-%d-%Y",
    "%Y/%m/%d %H:%M:%S",
]


def random_timestamp():
    base = datetime(2024, 1, 1) + timedelta(minutes=random.randint(0, 525600))
    fmt = random.choice(TS_FORMATS)
    return base.strftime(fmt)


def random_mileage():
    val = round(np.random.uniform(0, 250000), 1)
    r = random.random()
    if r < 0.05:
        return ""
    if r < 0.10:
        return f"{val} mi"
    if r < 0.13:
        return "N/A"
    if r < 0.16:
        return -abs(val)
    return val


def random_fuel():
    val = round(np.random.uniform(0, 100), 1)
    r = random.random()
    if r < 0.05:
        return ""
    if r < 0.09:
        return f"{val}%"
    if r < 0.12:
        return "unknown"
    if r < 0.15:
        return round(np.random.uniform(101, 150), 1)
    return val


def random_vehicle_id():
    if random.random() < 0.03:
        return random.choice(["", "VEH-XXXX", "  "])
    return random.choice(VEHICLE_IDS)


def random_driver_id():
    if random.random() < 0.04:
        return None
    return random.choice(DRIVER_IDS)


def random_location():
    return random.choice(LOCATIONS)


def build_rows(n):
    rows = []
    for _ in range(n):
        rows.append(
            {
                "vehicle_id": random_vehicle_id(),
                "fuel_level": random_fuel(),
                "mileage": random_mileage(),
                "timestamp": random_timestamp(),
                "location": random_location(),
                "driver_id": random_driver_id(),
            }
        )
    return rows


def main():
    rows = build_rows(N)
    df = pd.DataFrame(rows)

    # inject exact duplicate rows
    dup_sample = df.sample(n=150, random_state=1)
    df = pd.concat([df, dup_sample], ignore_index=True)

    # inject duplicate timestamps with different other fields
    dup_ts_idx = df.sample(n=80, random_state=2).index
    fixed_ts = "2024-06-15 12:00:00"
    df.loc[dup_ts_idx, "timestamp"] = fixed_ts

    df = df.sample(frac=1, random_state=3).reset_index(drop=True)

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_PATH, index=False)
    print(f"Generated {len(df)} raw records -> {RAW_PATH}")


if __name__ == "__main__":
    main()

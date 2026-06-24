"""Ingest raw fleet CSV -> validate/clean -> write Parquet cleaned zone."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW_PATH = BASE / "data" / "raw" / "fleet_raw.csv"
CLEANED_PATH = BASE / "data" / "cleaned" / "fleet_processed.parquet"

VALID_VEHICLE_RE = re.compile(r"^VEH-\d{4}$")
VALID_DRIVER_RE = re.compile(r"^DRV-\d{4}$")


def clean_numeric(series: pd.Series) -> pd.Series:
    """Strip units/symbols, coerce to float, drop negatives/invalid."""
    cleaned = (
        series.astype(str)
        .str.replace(r"[^0-9.\-]", "", regex=True)
        .replace("", np.nan)
    )
    out = pd.to_numeric(cleaned, errors="coerce")
    out = out.where(out >= 0)
    return out


def main():
    metrics = {}

    df = pd.read_csv(RAW_PATH, dtype=str)
    metrics["records_ingested"] = len(df)

    # exact duplicate rows
    exact_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    metrics["exact_duplicates_removed"] = int(exact_dupes)

    # normalize vehicle_id / driver_id
    df["vehicle_id"] = df["vehicle_id"].str.strip()
    df.loc[~df["vehicle_id"].str.match(VALID_VEHICLE_RE, na=False), "vehicle_id"] = np.nan

    df["driver_id"] = df["driver_id"].astype(str).str.strip()
    df.loc[~df["driver_id"].str.match(VALID_DRIVER_RE, na=False), "driver_id"] = np.nan

    invalid_vehicle = df["vehicle_id"].isna().sum()
    metrics["invalid_vehicle_ids_flagged"] = int(invalid_vehicle)
    df = df.dropna(subset=["vehicle_id"])

    # normalize timestamp (multiple input formats)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", format="mixed")
    bad_ts = df["timestamp"].isna().sum()
    metrics["invalid_timestamps_dropped"] = int(bad_ts)
    df = df.dropna(subset=["timestamp"])

    # duplicate timestamps (per vehicle) -> keep first occurrence
    dup_ts_mask = df.duplicated(subset=["vehicle_id", "timestamp"])
    metrics["duplicate_timestamps_removed"] = int(dup_ts_mask.sum())
    df = df[~dup_ts_mask]

    # numeric fields
    df["mileage"] = clean_numeric(df["mileage"])
    df["fuel_level"] = clean_numeric(df["fuel_level"])
    df.loc[df["fuel_level"] > 100, "fuel_level"] = np.nan

    missing_mileage = df["mileage"].isna().sum()
    missing_fuel = df["fuel_level"].isna().sum()
    metrics["missing_mileage_imputed"] = int(missing_mileage)
    metrics["missing_fuel_imputed"] = int(missing_fuel)

    df["mileage"] = df.groupby("vehicle_id")["mileage"].transform(
        lambda s: s.fillna(s.median())
    )
    df["fuel_level"] = df.groupby("vehicle_id")["fuel_level"].transform(
        lambda s: s.fillna(s.median())
    )
    df["mileage"] = df["mileage"].fillna(df["mileage"].median())
    df["fuel_level"] = df["fuel_level"].fillna(df["fuel_level"].median())

    # normalize location
    df["location"] = df["location"].replace(
        {"": "UNKNOWN", "n/a": "UNKNOWN", "N/A": "UNKNOWN", "nan": "UNKNOWN"}
    )
    df["location"] = df["location"].fillna("UNKNOWN")

    # driver_id missing -> explicit placeholder
    unassigned_drivers = df["driver_id"].isna().sum()
    metrics["unassigned_drivers"] = int(unassigned_drivers)
    df["driver_id"] = df["driver_id"].fillna("UNASSIGNED")

    df = df.sort_values("timestamp").reset_index(drop=True)
    metrics["records_final"] = len(df)

    CLEANED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEANED_PATH, index=False)

    print("=" * 50)
    print("FLEET DATA INGESTION SUMMARY")
    print("=" * 50)
    for k, v in metrics.items():
        print(f"{k.replace('_', ' ').capitalize()}: {v}")
    print(f"Cleaned data written to: {CLEANED_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()

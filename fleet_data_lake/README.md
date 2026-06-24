# Fleet Data Lake Ingestion Pipeline

End-to-end mock data lake pipeline: generates a messy raw fleet dataset (Raw Zone),
then validates/cleans it into a Parquet Cleaned Zone.

## Prerequisites

- Python 3.9+
- pip

## Install requirements

```bash
cd fleet_data_lake
pip install -r requirements.txt
```

## 1. Generate mock raw data (Raw Zone)

```bash
python scripts/generate_mock_data.py
```

Creates `data/raw/fleet_raw.csv` with 5,000+ messy records: missing values,
duplicates, invalid numeric formats, bad timestamps, inconsistent locations.

## 2. Run the ingestion pipeline (Cleaned Zone)

```bash
python scripts/pipeline.py
```

Reads `data/raw/fleet_raw.csv`, validates/cleans it, and writes
`data/cleaned/fleet_processed.parquet`. Prints an ingestion summary report
(records ingested, duplicates removed, invalid records dropped, values
imputed, final record count).

## Data Lake Layout

```
fleet_data_lake/
├── data/
│   ├── raw/
│   │   └── fleet_raw.csv            # Raw Zone - untouched ingested data
│   └── cleaned/
│       └── fleet_processed.parquet  # Cleaned Zone - validated/typed data
├── scripts/
│   ├── generate_mock_data.py
│   └── pipeline.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Cleaning logic

- Drops exact duplicate rows
- Validates `vehicle_id`/`driver_id` format (`VEH-####` / `DRV-####`), drops
  invalid vehicle rows, marks missing drivers `UNASSIGNED`
- Parses mixed-format timestamps, drops unparseable rows, removes duplicate
  `(vehicle_id, timestamp)` pairs
- Strips units/symbols from `mileage`/`fuel_level`, coerces to numeric,
  discards out-of-range values, imputes missing values with per-vehicle
  median (falls back to global median)
- Normalizes inconsistent `location` values to `UNKNOWN`

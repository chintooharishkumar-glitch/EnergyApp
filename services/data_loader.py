from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd

REQUIRED_COLUMNS = ["timestamp", "room_id", "device_type", "status", "occupancy"]


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise and validate required columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("Some timestamps could not be parsed. Please check the input file.")

    df["room_id"] = df["room_id"].astype(str)
    df["device_type"] = df["device_type"].astype(str).str.upper()

    if pd.api.types.is_numeric_dtype(df["status"]):
        df["is_on"] = df["status"].astype(int) == 1
    else:
        df["is_on"] = df["status"].astype(str).str.upper().isin(["ON", "1", "TRUE"])

    if pd.api.types.is_numeric_dtype(df["occupancy"]):
        df["is_occupied"] = df["occupancy"].astype(int) == 1
    else:
        df["is_occupied"] = df["occupancy"].astype(str).str.upper().isin(["1", "TRUE", "YES"])

    df = df.sort_values("timestamp")

    # Estimate interval in hours based on median difference.
    diffs = df["timestamp"].diff().dropna()
    if diffs.empty:
        interval_hours = 1 / 12  # default 5 minutes
    else:
        interval_hours = diffs.median().total_seconds() / 3600
    df["interval_hours"] = interval_hours

    return df


def load_uploaded_file(file: IO[bytes]) -> pd.DataFrame:
    """Load data from an uploaded CSV/Excel file."""
    name = getattr(file, "name", "uploaded_file")
    suffix = Path(name).suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(file)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    return _normalise_columns(df)


def load_sample_data() -> pd.DataFrame:
    """Load bundled sample data from sample_data/sample_classroom_data.csv."""
    sample_path = Path(__file__).parent.parent / "sample_data" / "sample_classroom_data.csv"
    if not sample_path.exists():
        raise FileNotFoundError("Sample data file not found.")

    df = pd.read_csv(sample_path)
    return _normalise_columns(df)


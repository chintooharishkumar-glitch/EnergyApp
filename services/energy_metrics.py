from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import pandas as pd


DEFAULT_DEVICE_POWER = {
    "LIGHT": 40.0,
    "AC": 1500.0,
}
DEFAULT_FALLBACK_POWER = 100.0


@dataclass
class SummaryMetrics:
    start: pd.Timestamp
    end: pd.Timestamp
    num_rooms: int
    total_energy_kwh: float
    total_cost: float
    total_wasted_kwh: float
    total_wasted_cost: float
    total_wasted_hours: float
    wasted_energy_pct: float


def _ensure_energy_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "power_watts" in df.columns:
        power = df["power_watts"].fillna(0).astype(float)
    else:
        device_type = df.get("device_type", "").astype(str).str.upper()
        power = device_type.map(DEFAULT_DEVICE_POWER).fillna(DEFAULT_FALLBACK_POWER)

    df["power_watts_effective"] = power
    df["energy_kwh"] = df["power_watts_effective"] * df["interval_hours"] / 1000.0
    df["is_wasted"] = df["is_on"] & (~df["is_occupied"])
    df["wasted_energy_kwh"] = df["energy_kwh"].where(df["is_wasted"], 0.0)
    df["wasted_hours"] = df["interval_hours"].where(df["is_wasted"], 0.0)
    return df


def filter_data_by_controls(
    df: pd.DataFrame,
    controls: Mapping[str, object],
) -> pd.DataFrame:
    result = df.copy()
    date_range: Iterable = controls.get("date_range") or ()
    if len(date_range) == 2:
        start_date, end_date = date_range
        result = result[
            (result["timestamp"].dt.date >= start_date)
            & (result["timestamp"].dt.date <= end_date)
        ]

    rooms = controls.get("rooms")
    if rooms:
        result = result[result["room_id"].isin(rooms)]

    devices = controls.get("devices")
    if devices:
        result = result[result["device_type"].isin(devices)]

    return result


def compute_overall_summary(df: pd.DataFrame, tariff_per_kwh: float) -> SummaryMetrics:
    df_e = _ensure_energy_columns(df)

    total_energy_kwh = float(df_e["energy_kwh"].sum())
    total_wasted_kwh = float(df_e["wasted_energy_kwh"].sum())
    total_wasted_hours = float(df_e["wasted_hours"].sum())

    total_cost = total_energy_kwh * tariff_per_kwh
    total_wasted_cost = total_wasted_kwh * tariff_per_kwh
    wasted_energy_pct = (total_wasted_kwh / total_energy_kwh * 100.0) if total_energy_kwh > 0 else 0.0

    return SummaryMetrics(
        start=df_e["timestamp"].min(),
        end=df_e["timestamp"].max(),
        num_rooms=int(df_e["room_id"].nunique()),
        total_energy_kwh=total_energy_kwh,
        total_cost=total_cost,
        total_wasted_kwh=total_wasted_kwh,
        total_wasted_cost=total_wasted_cost,
        total_wasted_hours=total_wasted_hours,
        wasted_energy_pct=wasted_energy_pct,
    )


def compute_room_level_metrics(df: pd.DataFrame, tariff_per_kwh: float) -> pd.DataFrame:
    df_e = _ensure_energy_columns(df)
    grouped = df_e.groupby("room_id", as_index=False).agg(
        energy_kwh=("energy_kwh", "sum"),
        wasted_energy_kwh=("wasted_energy_kwh", "sum"),
        wasted_hours=("wasted_hours", "sum"),
    )
    grouped["wasted_pct"] = grouped["wasted_energy_kwh"] / grouped["energy_kwh"].where(
        grouped["energy_kwh"] > 0,
        1.0,
    ) * 100.0
    grouped["cost"] = grouped["energy_kwh"] * tariff_per_kwh
    grouped["wasted_cost"] = grouped["wasted_energy_kwh"] * tariff_per_kwh
    return grouped


def compute_device_level_metrics(df: pd.DataFrame, tariff_per_kwh: float) -> pd.DataFrame:
    df_e = _ensure_energy_columns(df)
    grouped = df_e.groupby(["room_id", "device_type"], as_index=False).agg(
        energy_kwh=("energy_kwh", "sum"),
        wasted_energy_kwh=("wasted_energy_kwh", "sum"),
        wasted_hours=("wasted_hours", "sum"),
    )
    grouped["wasted_pct"] = grouped["wasted_energy_kwh"] / grouped["energy_kwh"].where(
        grouped["energy_kwh"] > 0,
        1.0,
    ) * 100.0
    grouped["cost"] = grouped["energy_kwh"] * tariff_per_kwh
    grouped["wasted_cost"] = grouped["wasted_energy_kwh"] * tariff_per_kwh
    return grouped


def compute_timeseries(df: pd.DataFrame, room_id: str) -> pd.DataFrame:
    df_room = df[df["room_id"] == room_id].copy()
    if df_room.empty:
        return df_room

    df_e = _ensure_energy_columns(df_room)
    ts = (
        df_e.set_index("timestamp")
        .resample("1H")
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            wasted_energy_kwh=("wasted_energy_kwh", "sum"),
        )
        .reset_index()
    )
    return ts


def compute_active_hours_matrix(df: pd.DataFrame) -> pd.DataFrame:
    df_e = df.copy()
    df_e["hour"] = df_e["timestamp"].dt.hour
    df_e["weekday"] = df_e["timestamp"].dt.day_name()
    pivot = (
        df_e.groupby(["weekday", "hour"])["is_on"]
        .mean()
        .reset_index()
        .pivot(index="weekday", columns="hour", values="is_on")
        .fillna(0.0)
    )
    return pivot


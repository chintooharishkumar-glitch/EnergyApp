from __future__ import annotations

import pandas as pd
import plotly.express as px

from services.energy_metrics import compute_timeseries, compute_active_hours_matrix


def usage_by_room_bar(room_metrics: pd.DataFrame):
    if room_metrics.empty:
        return px.bar(title="No data to display")
    fig = px.bar(
        room_metrics,
        x="room_id",
        y="energy_kwh",
        labels={"room_id": "Room", "energy_kwh": "Energy (kWh)"},
        title="Total energy usage by room",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=40))
    return fig


def wasted_cost_by_room_bar(room_metrics: pd.DataFrame):
    if room_metrics.empty:
        return px.bar(title="No data to display")
    fig = px.bar(
        room_metrics.sort_values("wasted_cost", ascending=False),
        x="room_id",
        y="wasted_cost",
        labels={"room_id": "Room", "wasted_cost": "Wasted cost"},
        title="Wasted cost by room",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=40))
    return fig


def usage_timeseries_line(df: pd.DataFrame, room_id: str):
    ts = compute_timeseries(df, room_id)
    if ts.empty:
        return px.line(title="No data to display")
    fig = px.line(
        ts,
        x="timestamp",
        y="energy_kwh",
        labels={"timestamp": "Time", "energy_kwh": "Energy (kWh)"},
        title=f"Hourly energy usage for room {room_id}",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=40))
    return fig


def active_hours_heatmap(df: pd.DataFrame):
    matrix = compute_active_hours_matrix(df)
    if matrix.empty:
        return px.imshow([[0]], labels=dict(x="Hour", y="Day", color="Active fraction"), title="No data")

    # Reorder weekdays for a nicer view if present.
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    index = [d for d in weekday_order if d in matrix.index]
    matrix = matrix.loc[index]

    fig = px.imshow(
        matrix,
        labels=dict(x="Hour of day", y="Day of week", color="Fraction ON"),
        aspect="auto",
        title="Fraction of time equipment is ON",
    )
    fig.update_xaxes(type="category")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=40))
    return fig


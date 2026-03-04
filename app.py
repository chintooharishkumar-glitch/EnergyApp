import streamlit as st

from services.data_loader import load_uploaded_file, load_sample_data
from services.energy_metrics import (
    filter_data_by_controls,
    compute_overall_summary,
    compute_room_level_metrics,
    compute_device_level_metrics,
)
from services.report_generator import build_pdf_report
from ui.layout import (
    render_app_header,
    render_kpi_row,
    render_empty_state,
)
from ui.charts import (
    usage_by_room_bar,
    wasted_cost_by_room_bar,
    usage_timeseries_line,
    active_hours_heatmap,
)


st.set_page_config(
    page_title="Smart Classroom Energy Monitor",
    page_icon="💡",
    layout="wide",
)


def get_data():
    return st.session_state.get("processed_data")


def main():
    render_app_header()

    page = st.sidebar.radio(
        "Navigate",
        ["Upload data", "Dashboard", "Wasted energy", "Reports"],
    )

    if page == "Upload data":
        render_upload_page()
    elif page == "Dashboard":
        render_dashboard_page()
    elif page == "Wasted energy":
        render_wasted_energy_page()
    elif page == "Reports":
        render_reports_page()


def render_upload_page():
    st.subheader("Upload classroom energy & occupancy data")
    st.write(
        "Upload a CSV/Excel file with timestamped readings, or load the sample dataset "
        "to explore the dashboard."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
        )
    with col2:
        if st.button("Load sample data"):
            with st.spinner("Loading sample data..."):
                df = load_sample_data()
                st.session_state["raw_data"] = df
                st.session_state["processed_data"] = df
                st.success("Sample data loaded.")

    if uploaded_file is not None:
        try:
            with st.spinner("Reading and validating file..."):
                df = load_uploaded_file(uploaded_file)
            st.session_state["raw_data"] = df
            st.session_state["processed_data"] = df
            st.success("File uploaded and validated successfully.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not load file: {exc}")

    data = get_data()
    if data is not None:
        st.markdown("### Data preview")
        st.dataframe(data.head(100))

        st.markdown("### Basic stats")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Records", f"{len(data):,}")
        with col_b:
            st.metric("Rooms", data["room_id"].nunique())
        with col_c:
            st.metric("Date range", f"{data['timestamp'].min().date()} → {data['timestamp'].max().date()}")
    else:
        render_empty_state(
            title="No data loaded yet",
            message="Upload a CSV/Excel file or click **Load sample data** to get started.",
        )


def render_filters():
    data = get_data()
    if data is None:
        return None

    st.sidebar.markdown("### Filters")
    min_ts = data["timestamp"].min()
    max_ts = data["timestamp"].max()

    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_ts.date(), max_ts.date()),
        min_value=min_ts.date(),
        max_value=max_ts.date(),
    )

    rooms = sorted(data["room_id"].unique())
    selected_rooms = st.sidebar.multiselect(
        "Rooms",
        options=rooms,
        default=rooms,
    )

    device_types = sorted(data["device_type"].unique())
    selected_devices = st.sidebar.multiselect(
        "Devices",
        options=device_types,
        default=device_types,
    )

    tariff = st.sidebar.number_input(
        "Tariff (per kWh)",
        min_value=0.0,
        value=0.12,
        step=0.01,
        help="Electricity cost per kWh used for cost calculations.",
    )

    controls = {
        "date_range": date_range,
        "rooms": selected_rooms,
        "devices": selected_devices,
        "tariff": float(tariff),
    }
    return controls


def render_dashboard_page():
    data = get_data()
    if data is None:
        render_empty_state(
            title="Upload data to see the dashboard",
            message="Go to **Upload data** and upload a CSV/Excel file or load the sample dataset.",
        )
        return

    controls = render_filters()
    if controls is None:
        return

    filtered = filter_data_by_controls(data, controls)
    if filtered.empty:
        render_empty_state(
            title="No data matching filters",
            message="Try widening the date range or selecting more rooms/devices.",
        )
        return

    summary = compute_overall_summary(filtered, controls["tariff"])
    room_metrics = compute_room_level_metrics(filtered, controls["tariff"])

    render_kpi_row(
        [
            ("Total energy (kWh)", f"{summary.total_energy_kwh:.2f}"),
            ("Total cost", f"${summary.total_cost:.2f}"),
            ("Rooms", str(summary.num_rooms)),
            ("Period", f"{summary.start.date()} → {summary.end.date()}"),
        ]
    )

    st.markdown("### Energy usage by room")
    fig_rooms = usage_by_room_bar(room_metrics)
    st.plotly_chart(fig_rooms, use_container_width=True)

    st.markdown("### Time-series usage")
    ordered_rooms = list(
        room_metrics.sort_values("energy_kwh", ascending=False)["room_id"].unique()
    )
    room_for_ts = st.selectbox(
        "Select room for time-series",
        options=ordered_rooms,
        index=0,
        help="By default, the room with the highest energy usage is shown.",
    )
    ts_fig = usage_timeseries_line(filtered, room_for_ts)
    st.plotly_chart(ts_fig, use_container_width=True)

    st.markdown("### Active hours heatmap")
    heatmap_fig = active_hours_heatmap(filtered)
    st.plotly_chart(heatmap_fig, use_container_width=True)


def render_wasted_energy_page():
    data = get_data()
    if data is None:
        render_empty_state(
            title="Upload data to see wasted energy",
            message="Go to **Upload data** and upload a CSV/Excel file or load the sample dataset.",
        )
        return

    controls = render_filters()
    if controls is None:
        return

    filtered = filter_data_by_controls(data, controls)
    if filtered.empty:
        render_empty_state(
            title="No data matching filters",
            message="Try widening the date range or selecting more rooms/devices.",
        )
        return

    summary = compute_overall_summary(filtered, controls["tariff"])
    room_metrics = compute_room_level_metrics(filtered, controls["tariff"])

    render_kpi_row(
        [
            ("Wasted kWh", f"{summary.total_wasted_kwh:.2f}"),
            ("Wasted cost", f"${summary.total_wasted_cost:.2f}"),
            ("Wasted hours", f"{summary.total_wasted_hours:.2f}"),
            ("Wasted % of energy", f"{summary.wasted_energy_pct:.1f}%"),
        ]
    )

    st.markdown("### Wasted cost by room")
    wasted_fig = wasted_cost_by_room_bar(room_metrics)
    st.plotly_chart(wasted_fig, use_container_width=True)

    st.markdown("### Rooms ranked by wasted cost")
    st.dataframe(
        room_metrics.sort_values("wasted_cost", ascending=False)[
            ["room_id", "energy_kwh", "wasted_energy_kwh", "wasted_hours", "wasted_cost", "wasted_pct"]
        ]
    )


def render_reports_page():
    data = get_data()
    if data is None:
        render_empty_state(
            title="Upload data to generate reports",
            message="Go to **Upload data** and upload a CSV/Excel file or load the sample dataset.",
        )
        return

    controls = render_filters()
    if controls is None:
        return

    filtered = filter_data_by_controls(data, controls)
    if filtered.empty:
        render_empty_state(
            title="No data matching filters",
            message="Try widening the date range or selecting more rooms/devices.",
        )
        return

    tariff = controls["tariff"]
    summary = compute_overall_summary(filtered, tariff)
    room_metrics = compute_room_level_metrics(filtered, tariff)
    device_metrics = compute_device_level_metrics(filtered, tariff)

    st.subheader("Generate PDF summary report")
    st.write("Configure the options below and click **Generate report** to download a PDF.")

    report_title = st.text_input(
        "Report title",
        value="Smart Classroom Energy Wastage Report",
    )

    if st.button("Generate PDF report"):
        with st.spinner("Building PDF report..."):
            pdf_bytes = build_pdf_report(
                title=report_title,
                summary=summary,
                room_metrics=room_metrics,
                device_metrics=device_metrics,
                controls=controls,
            )
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name="smart_classroom_energy_report.pdf",
            mime="application/pdf",
        )


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Smart Energy Monitor", layout="wide")

st.title("⚡ Smart Classroom Energy Monitoring Dashboard")

file = st.file_uploader("Upload Energy CSV", type="csv")

if file:

    data = pd.read_csv(file)

    data["Wasted"] = ((data["Occupied"]==0) &
                      ((data["LightOn"]==1)|(data["ACOn"]==1)))

    report = data.groupby("Classroom")["Wasted"].sum()

    st.subheader("Dataset")
    st.dataframe(data)

    st.subheader("Energy Waste Bar Chart")
    st.bar_chart(report)

    st.subheader("Waste Distribution (Pie)")
    st.pyplot(report.plot.pie(autopct="%1.1f%%").get_figure())

    st.success("Analysis Complete ✅")

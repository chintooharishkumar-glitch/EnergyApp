from __future__ import annotations

import streamlit as st


def render_app_header() -> None:
    left, right = st.columns([4, 1])
    with left:
        st.title("Smart Classroom Energy Monitor")
        st.caption(
            "Detect wasted energy when lights and AC are ON in empty classrooms, "
            "and turn insights into real cost savings."
        )
    with right:
        st.markdown(
            "<div style='text-align:right; font-size:13px; opacity:0.8;'>"
            "Smart campus · Sustainability · Analytics"
            "</div>",
            unsafe_allow_html=True,
        )


def render_kpi_row(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items, strict=False):
        with col:
            st.metric(label, value)


def render_empty_state(title: str, message: str) -> None:
    st.markdown(
        f"""
        <div style="
            border-radius:10px;
            border:1px dashed rgba(0,0,0,0.1);
            padding:1.5rem;
            background-color:rgba(240,248,255,0.5);
        ">
            <h3 style="margin-top:0;">{title}</h3>
            <p style="margin-bottom:0;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


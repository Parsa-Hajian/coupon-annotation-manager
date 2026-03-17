"""Coupon Annotation Management App — Main entry point."""

import os
import streamlit as st

st.set_page_config(
    page_title="Coupon Annotation Manager",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the default Streamlit top-left hamburger/pages menu
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Logo in sidebar — centered
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
if os.path.exists(logo_path):
    st.sidebar.markdown(
        "<div style='text-align: center;'>",
        unsafe_allow_html=True,
    )
    st.sidebar.image(logo_path, width=150)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Ensure SQLite tables exist on first run
from bq_client import ensure_tables_exist, sync_status_log, _fetch_all_coupons_brands

if "tables_initialized" not in st.session_state:
    ensure_tables_exist()
    st.session_state["tables_initialized"] = True

# Preload + cache BQ data on first run
if "data_preloaded" not in st.session_state:
    with st.spinner("Loading coupon data..."):
        _fetch_all_coupons_brands()
    st.session_state["data_preloaded"] = True

# Sync status log — only once per session
if "status_synced" not in st.session_state:
    sync_status_log()
    st.session_state["status_synced"] = True

# Initialize page state
if "page" not in st.session_state:
    st.session_state["page"] = "Browse Coupons"

# Notification badge
from components.notification_badge import render_notification_badge
render_notification_badge()

# Navigation — buttons only
st.sidebar.title("Coupon Manager")

PAGES = ["Browse Coupons", "Coupon Detail", "Export", "History"]
for page_name in PAGES:
    if st.sidebar.button(
        page_name,
        use_container_width=True,
        type="primary" if st.session_state["page"] == page_name else "secondary",
    ):
        st.session_state["page"] = page_name
        st.rerun()

st.sidebar.divider()
st.sidebar.caption("UniversityBox — Coupon Annotation Tool")

# Render selected page
page = st.session_state["page"]
if page == "Browse Coupons":
    from pages.coupon_browser import render
    render()
elif page == "Coupon Detail":
    from pages.coupon_detail import render
    render()
elif page == "Export":
    from pages.export import render
    render()
elif page == "History":
    from pages.history import render
    render()

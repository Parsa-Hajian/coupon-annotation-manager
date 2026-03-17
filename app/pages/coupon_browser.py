"""Page 1: Browse, search, and filter coupons. Click row to select."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st
from bq_client import get_coupons

ROWS_PER_PAGE = 50

BRAND_MACRO_FALLBACK = {
    "samsung": "Technology", "huawei": "Technology", "apple": "Technology",
    "xiaomi": "Technology", "lenovo": "Technology", "hp": "Technology",
    "dell": "Technology", "asus": "Technology", "sony": "Technology",
    "lg": "Technology", "microsoft": "Technology", "google": "Technology",
    "amazon": "Technology", "nike": "Fashion", "adidas": "Fashion",
    "zara": "Fashion", "h&m": "Fashion", "puma": "Fashion", "gucci": "Fashion",
    "just eat": "Food", "deliveroo": "Food", "uber eats": "Food",
    "glovo": "Food", "mcdonald's": "Food", "domino's": "Food",
    "starbucks": "Food", "ikea": "House", "leroy merlin": "House",
    "netflix": "Media", "spotify": "Media", "disney+": "Media",
    "tim": "Media", "vodafone": "Media", "wind tre": "Media",
    "booking.com": "Travel", "airbnb": "Travel", "ryanair": "Travel",
    "italo": "Travel", "trenitalia": "Travel", "flixbus": "Travel",
    "sephora": "Health", "douglas": "Health", "myprotein": "Health",
    "udemy": "Education", "coursera": "Education",
    "eventbrite": "Culture", "ticketone": "Culture",
    "ebay": "Market Places", "subito": "Market Places", "vinted": "Market Places",
}


def render():
    st.header("Coupon Browser")

    # Filters
    col1, col2 = st.columns([1, 3])
    with col1:
        time_filter = st.radio(
            "Time Period",
            ["Past Month", "Past Week", "Today", "Custom", "All"],
            index=0,
        )
    with col2:
        search = st.text_input(
            "Search (by name, brand, category, or coupon ID)",
            value="",
            placeholder="Type to search...",
        )

    # Custom date range
    custom_start = None
    custom_end = None
    if time_filter == "Custom":
        dc1, dc2 = st.columns(2)
        with dc1:
            custom_start = st.date_input("Start Date", value=date.today() - timedelta(days=30), key="browser_start")
        with dc2:
            custom_end = st.date_input("End Date", value=date.today(), key="browser_end")
        if custom_start > custom_end:
            st.error("Start date must be before end date.")
            return

    df = get_coupons(time_filter=time_filter, search=search,
                     custom_start=str(custom_start) if custom_start else None,
                     custom_end=str(custom_end) if custom_end else None)

    if df.empty:
        st.info("No coupons found for the selected filters.")
        return

    # Build display columns
    industry = df["industry"].fillna("")
    suggested = df["brand_name"].map(
        lambda x: BRAND_MACRO_FALLBACK.get(str(x).strip().lower(), "") if x else ""
    )
    display_cat = industry.copy()
    missing_mask = display_cat == ""
    display_cat[missing_mask & (suggested != "")] = suggested[missing_mask & (suggested != "")] + " (suggested)"
    display_cat[missing_mask & (suggested == "")] = "\u2014"

    processed_str = df["is_processed"].map({True: "\u2705", False: "\u274c"})

    display_df = pd.DataFrame({
        "ID": df["coupon_id"],
        "Brand ID": df["brand_id"],
        "Coupon Name": df["coupon_name"],
        "Brand": df["brand_name"],
        "Category": display_cat,
        "Created": df["created_time"],
        "Status": df["status"],
        "Processed": processed_str,
    })

    total = len(display_df)
    st.caption(f"{total} coupons found")

    # Pagination
    total_pages = max(1, (total + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    if total > ROWS_PER_PAGE:
        page_num = st.number_input(
            f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1, key="browser_page"
        )
    else:
        page_num = 1

    start_idx = (page_num - 1) * ROWS_PER_PAGE
    end_idx = min(start_idx + ROWS_PER_PAGE, total)
    page_df = display_df.iloc[start_idx:end_idx].reset_index(drop=True)

    # Selectable dataframe — click a row to highlight it
    event = st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="coupon_table",
    )

    if total > ROWS_PER_PAGE:
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {total}")

    # Show selected row info + action buttons
    selected_rows = event.selection.rows if event.selection else []
    if selected_rows:
        sel_idx = selected_rows[0]
        sel_row = page_df.iloc[sel_idx]
        cid = int(sel_row["ID"])

        st.success(f"Selected: **{sel_row['Coupon Name']}** (ID: {cid}, Brand: {sel_row['Brand']})")

        col_select, col_edit = st.columns(2)
        with col_select:
            if st.button("Open Coupon Detail", type="primary", use_container_width=True):
                st.session_state["selected_coupon_id"] = cid
                st.session_state["form_coupon_id"] = None
                st.session_state["page"] = "Coupon Detail"
                st.rerun()
        with col_edit:
            if sel_row["Processed"] == "\u2705":
                if st.button("Edit Annotation", use_container_width=True):
                    st.session_state["selected_coupon_id"] = cid
                    st.session_state["form_coupon_id"] = None
                    st.session_state["page"] = "Coupon Detail"
                    st.rerun()

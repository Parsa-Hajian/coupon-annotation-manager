"""Page 4: Activity history — view annotation logs for any period."""

from datetime import date, timedelta

import streamlit as st
from bq_client import get_activity_log


def render():
    st.header("Annotation History")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=30), key="hist_start")
    with col2:
        end_date = st.date_input("To", value=date.today(), key="hist_end")

    if start_date > end_date:
        st.error("Start date must be before end date.")
        return

    df = get_activity_log(str(start_date), str(end_date))

    if df.empty:
        st.info("No annotation activity found for this period.")
        return

    st.caption(f"{len(df)} annotations in this period")

    st.dataframe(
        df.rename(columns={
            "coupon_id": "Coupon ID",
            "coupon_name": "Coupon Name",
            "brand_name": "Brand",
            "processed_by": "Processed By",
            "processed_at": "Processed At",
        }),
        use_container_width=True,
        hide_index=True,
    )

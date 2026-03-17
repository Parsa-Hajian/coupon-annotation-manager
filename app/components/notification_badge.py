"""Red notification badge for unprocessed active coupons."""

import streamlit as st
from bq_client import count_unprocessed_active


def render_notification_badge():
    """Show a red alarm badge in the sidebar with the count of unprocessed active coupons."""
    count = count_unprocessed_active()
    if count > 0:
        st.sidebar.markdown(
            f"""
            <div style="
                background-color: #ff4b4b;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 10px;
            ">
                {count} unprocessed coupon{"s" if count != 1 else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.success("All active coupons processed!")

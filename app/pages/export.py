"""Page 3: Static Excel file with Update button."""

import io
import os

import pandas as pd
import streamlit as st
from bq_client import get_all_export_data, get_status_history

EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "coupon_annotations.xlsx")


def _pivot_to_excel_format(df: pd.DataFrame, status_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot discount blocks and product categories into wide-format columns per coupon."""
    if df.empty:
        return df

    coupon_ids = df["coupon_id"].unique()

    rows = []
    for cid in coupon_ids:
        coupon_rows = df[df["coupon_id"] == cid]
        first = coupon_rows.iloc[0]

        row = {
            "Coupon ID": first["coupon_id"],
            "Brand ID": first.get("brand_id"),
            "Title": first["title"],
            "Brand": first["brand"],
            "Brand Category": first["brand_category"],
            "Created Time": first["created_time"],
            "Active Status": first["active_status"],
            "Last Modified": first["last_modified"],
            "Processed By": first["processed_by"],
            "Processed At": first["processed_at"],
        }

        # Add status history (deactivation/reactivation times)
        if not status_df.empty:
            coupon_status = status_df[status_df["coupon_id"] == cid].sort_values("changed_at")
            deactivation_times = coupon_status[coupon_status["status"] == "Non attivo"]["changed_at"].tolist()
            reactivation_times = coupon_status[coupon_status["status"] == "Attivo"]["changed_at"].tolist()

            # Skip the first "Attivo" if it's the initial state
            if reactivation_times and (not deactivation_times or reactivation_times[0] < deactivation_times[0]):
                reactivation_times = reactivation_times[1:]

            for j, dt in enumerate(deactivation_times):
                row[f"Deactivation Time {j + 1}"] = dt
            for j, dt in enumerate(reactivation_times):
                row[f"Reactivation Time {j + 1}"] = dt

        # Product categories — deduplicate
        unique_cats = coupon_rows[["product_macro_category", "product_sub_category", "product_micro_category"]].drop_duplicates()
        for j, (_, cat_row) in enumerate(unique_cats.iterrows()):
            prefix = f"Product {j + 1}"
            row[f"{prefix} Macro"] = cat_row["product_macro_category"]
            row[f"{prefix} Sub"] = cat_row["product_sub_category"]
            row[f"{prefix} Micro"] = cat_row["product_micro_category"]

        # Discount blocks — deduplicate
        disc_cols = ["discount_type", "discount_modifier", "discount_value_1", "discount_value_2",
                     "discount_values_json", "gift_is_product", "gift_macro_category",
                     "gift_sub_category", "gift_micro_category"]
        unique_discs = coupon_rows[disc_cols].drop_duplicates()
        for j, (_, disc_row) in enumerate(unique_discs.iterrows()):
            prefix = f"Discount {j + 1}"
            row[f"{prefix} Type"] = disc_row["discount_type"]
            row[f"{prefix} Modifier"] = disc_row["discount_modifier"]
            row[f"{prefix} Value 1"] = disc_row["discount_value_1"]
            row[f"{prefix} Value 2"] = disc_row["discount_value_2"]
            row[f"{prefix} Values (incremental)"] = disc_row["discount_values_json"]
            if disc_row["gift_is_product"]:
                row[f"{prefix} Gift Macro"] = disc_row["gift_macro_category"]
                row[f"{prefix} Gift Sub"] = disc_row["gift_sub_category"]
                row[f"{prefix} Gift Micro"] = disc_row["gift_micro_category"]

        rows.append(row)

    return pd.DataFrame(rows)


def _write_excel(export_df: pd.DataFrame):
    """Write DataFrame to the persistent Excel file, stripping timezones."""
    excel_df = export_df.copy()
    for col in excel_df.columns:
        if pd.api.types.is_datetime64_any_dtype(excel_df[col]):
            excel_df[col] = excel_df[col].dt.tz_localize(None)
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        excel_df.to_excel(writer, sheet_name="Coupon Annotations", index=False)


def render():
    st.header("Export Processed Coupons")

    # Show current file status
    if os.path.exists(EXCEL_PATH):
        mod_time = pd.Timestamp.fromtimestamp(os.path.getmtime(EXCEL_PATH))
        st.caption(f"Excel file last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("No Excel file generated yet. Click Update to create it.")

    if st.button("Update Excel", type="primary", use_container_width=True):
        with st.spinner("Fetching all processed annotations..."):
            df = get_all_export_data()

            if df.empty:
                st.info("No processed coupons found. Annotate some coupons first.")
                return

            coupon_ids = df["coupon_id"].unique().tolist()
            status_df = get_status_history(coupon_ids)
            export_df = _pivot_to_excel_format(df, status_df)

            _write_excel(export_df)
            st.session_state["export_df"] = export_df

        st.success(f"Excel file updated with {len(export_df)} coupons at: {EXCEL_PATH}")

    # Always show preview + download if file exists
    if "export_df" not in st.session_state and os.path.exists(EXCEL_PATH):
        st.session_state["export_df"] = pd.read_excel(EXCEL_PATH)

    if "export_df" in st.session_state and st.session_state["export_df"] is not None:
        export_df = st.session_state["export_df"]
        st.subheader(f"Preview ({len(export_df)} coupons)")
        st.dataframe(export_df, use_container_width=True, hide_index=True)

        # Offer download from the persistent file
        if os.path.exists(EXCEL_PATH):
            with open(EXCEL_PATH, "rb") as f:
                st.download_button(
                    label="Download Excel",
                    data=f.read(),
                    file_name="coupon_annotations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

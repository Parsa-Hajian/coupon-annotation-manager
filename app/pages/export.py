"""Page 3: Static Excel file with Update button + data visualization with modify/delete."""

import io
import os

import pandas as pd
import streamlit as st
from bq_client import get_all_export_data, get_status_history, delete_annotation

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

    # --- Update Excel section ---
    if os.path.exists(EXCEL_PATH):
        mod_time = pd.Timestamp.fromtimestamp(os.path.getmtime(EXCEL_PATH))
        st.caption(f"Excel file last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("No Excel file generated yet. Click Update to create it.")

    col_update, col_download = st.columns([3, 1])
    with col_update:
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

            st.success(f"Excel updated with {len(export_df)} coupons.")

    with col_download:
        if os.path.exists(EXCEL_PATH):
            with open(EXCEL_PATH, "rb") as f:
                st.download_button(
                    label="Download Excel",
                    data=f.read(),
                    file_name="coupon_annotations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    st.divider()

    # --- Data Visualization section ---
    st.subheader("Data Visualization")

    # Load data if not in session
    if "export_df" not in st.session_state and os.path.exists(EXCEL_PATH):
        st.session_state["export_df"] = pd.read_excel(EXCEL_PATH)

    if "export_df" not in st.session_state or st.session_state["export_df"] is None:
        st.info("No data to display. Click 'Update Excel' first.")
        return

    export_df = st.session_state["export_df"]
    st.caption(f"{len(export_df)} coupons")

    # Selectable table
    event = st.dataframe(
        export_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="export_table",
    )

    selected_rows = event.selection.rows if event.selection else []

    if selected_rows:
        sel_idx = selected_rows[0]
        sel_row = export_df.iloc[sel_idx]
        coupon_id = int(sel_row["Coupon ID"])
        st.success(f"Selected: **{sel_row.get('Title', '')}** (Coupon ID: {coupon_id})")

        col_modify, col_delete = st.columns(2)

        with col_modify:
            if st.button("Modify", type="primary", use_container_width=True):
                st.session_state["export_editing_idx"] = sel_idx
                st.session_state["export_editing_coupon_id"] = coupon_id

        with col_delete:
            if st.button("Delete", type="secondary", use_container_width=True):
                st.session_state["export_confirm_delete"] = coupon_id

    # --- Delete confirmation ---
    if st.session_state.get("export_confirm_delete"):
        cid = st.session_state["export_confirm_delete"]
        st.warning(f"Are you sure you want to delete the annotation for Coupon ID {cid}?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", type="primary"):
                delete_annotation(cid)
                # Remove from session dataframe
                export_df = export_df[export_df["Coupon ID"] != cid].reset_index(drop=True)
                st.session_state["export_df"] = export_df
                if not export_df.empty:
                    _write_excel(export_df)
                elif os.path.exists(EXCEL_PATH):
                    os.remove(EXCEL_PATH)
                st.session_state["export_confirm_delete"] = None
                st.session_state.pop("export_editing_idx", None)
                st.success("Annotation deleted.")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state["export_confirm_delete"] = None
                st.rerun()

    # --- Inline modify form ---
    if st.session_state.get("export_editing_idx") is not None:
        idx = st.session_state["export_editing_idx"]
        if idx < len(export_df):
            st.divider()
            st.subheader("Edit Row")
            row = export_df.iloc[idx]

            edited_values = {}
            cols_per_row = 3
            col_names = list(export_df.columns)
            for i in range(0, len(col_names), cols_per_row):
                batch = col_names[i:i + cols_per_row]
                cols = st.columns(len(batch))
                for j, col_name in enumerate(batch):
                    with cols[j]:
                        val = row[col_name]
                        if pd.isna(val):
                            val = ""
                        edited_values[col_name] = st.text_input(
                            col_name, value=str(val), key=f"edit_{col_name}_{idx}"
                        )

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Changes", type="primary", use_container_width=True):
                    for col_name, new_val in edited_values.items():
                        export_df.at[idx, col_name] = new_val
                    st.session_state["export_df"] = export_df
                    _write_excel(export_df)
                    st.session_state["export_editing_idx"] = None
                    st.success("Changes saved.")
                    st.rerun()
            with col_cancel:
                if st.button("Cancel Edit", use_container_width=True):
                    st.session_state["export_editing_idx"] = None
                    st.rerun()

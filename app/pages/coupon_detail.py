"""Page 2: Coupon detail view — product-by-product annotation form with visibility."""

import streamlit as st
from bq_client import (
    get_coupon_detail, get_existing_annotation, save_annotation,
    delete_annotation, save_visibility_schedule, delete_visibility_schedule,
)
from components.category_picker import render_category_picker
from components.discount_form import render_discount_block
from categories import MACRO_CATEGORIES

VISIBILITY_OPTIONS = ["", "High", "Medium", "Low"]


def _init_form_state(coupon_id: int):
    """Initialize or load form state for the selected coupon."""
    if st.session_state.get("form_coupon_id") == coupon_id:
        return

    st.session_state["form_coupon_id"] = coupon_id

    existing = get_existing_annotation(coupon_id)
    if existing:
        st.session_state["products"] = existing["products"]
        st.session_state["visibility"] = existing.get("visibility", "")
        st.session_state["visibility_schedules"] = existing.get("visibility_schedules", [])
        st.session_state["form_loaded_from_db"] = True
    else:
        st.session_state["products"] = [
            {"product_name": "", "product_macro_category": "", "product_sub_category": "",
             "product_micro_category": "", "discounts": [{}]}
        ]
        st.session_state["visibility"] = ""
        st.session_state["visibility_schedules"] = []
        st.session_state["form_loaded_from_db"] = False


def render():
    coupon_id = st.session_state.get("selected_coupon_id")
    if not coupon_id:
        st.warning("No coupon selected. Go to the Browser page to select one.")
        if st.button("Go to Browser"):
            st.session_state["page"] = "Browse Coupons"
            st.rerun()
        return

    detail = get_coupon_detail(coupon_id)
    if not detail:
        st.error(f"Coupon ID {coupon_id} not found.")
        return

    # Back button
    if st.button("< Back to Browser"):
        st.session_state.pop("form_coupon_id", None)
        st.session_state["page"] = "Browse Coupons"
        st.rerun()

    # Coupon info card
    st.header(f"Coupon: {detail['coupon_name']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Coupon ID", detail["coupon_id"])
        st.text(f"Brand: {detail.get('brand_name') or '\u2014'}")
        st.text(f"Brand ID: {detail.get('brand_id') or '\u2014'}")
    with col2:
        industry = detail.get("industry")
        if industry:
            st.text(f"Brand Category: {industry}")
        else:
            st.warning("Brand category is missing!")
        st.text(f"Type: {detail.get('tipologia') or '\u2014'}")
    with col3:
        st.text(f"Status: {detail.get('status') or '\u2014'}")
        st.text(f"Created: {detail.get('created_time', '\u2014')}")

    if detail.get("publish_date"):
        st.text(f"Published: {detail['publish_date']}  |  Expires: {detail.get('expiry_date') or '\u2014'}")

    st.divider()

    # Initialize form
    _init_form_state(coupon_id)

    # --- Operator name ---
    operator = st.text_input(
        "Operator Name",
        value=st.session_state.get("operator_name", ""),
        key="operator_input",
    )
    st.session_state["operator_name"] = operator

    if st.session_state.get("form_loaded_from_db"):
        st.info("This coupon has already been annotated. You can edit and re-save, or delete the annotation.")

    # --- Brand Category (editable if NULL) ---
    brand_category = detail.get("industry") or ""
    if not brand_category:
        st.subheader("Brand Category (missing \u2014 please select)")
        brand_category = st.selectbox(
            "Select brand macro category",
            [""] + MACRO_CATEGORIES,
            index=0,
            key="brand_category_select",
        )
        st.session_state["override_brand_category"] = brand_category
    else:
        st.session_state["override_brand_category"] = brand_category

    st.divider()

    # --- Visibility ---
    st.subheader("Visibility")
    vis_col1, vis_col2 = st.columns(2)

    with vis_col1:
        current_vis = st.session_state.get("visibility", "")
        vis_idx = VISIBILITY_OPTIONS.index(current_vis) if current_vis in VISIBILITY_OPTIONS else 0
        visibility = st.selectbox(
            "Position on website",
            VISIBILITY_OPTIONS,
            index=vis_idx,
            key="visibility_select",
            format_func=lambda x: x if x else "— Select —",
        )

    with vis_col2:
        show_schedule = st.checkbox("Schedule automated change", key="show_vis_schedule")

    if show_schedule:
        st.markdown("**Schedule a visibility change**")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sched_to = st.selectbox(
                "Change to",
                ["High", "Medium", "Low"],
                key="sched_vis_to",
            )
        with sc2:
            sched_date = st.date_input("On date", key="sched_vis_date")
        with sc3:
            sched_time = st.time_input("At time", key="sched_vis_time")

        if st.button("Add Schedule", key="add_vis_schedule"):
            from datetime import datetime as dt
            scheduled_at = dt.combine(sched_date, sched_time).isoformat()
            save_visibility_schedule(
                coupon_id, visibility or "", sched_to,
                scheduled_at, operator.strip(),
            )
            st.success(f"Scheduled: change to {sched_to} on {sched_date} at {sched_time}")
            # Refresh schedules
            existing = get_existing_annotation(coupon_id)
            if existing:
                st.session_state["visibility_schedules"] = existing.get("visibility_schedules", [])
            st.rerun()

    # Show existing schedules
    schedules = st.session_state.get("visibility_schedules", [])
    if schedules:
        st.markdown("**Pending schedules:**")
        for s in schedules:
            sc_col1, sc_col2 = st.columns([4, 1])
            with sc_col1:
                st.text(f"{s.get('visibility_from', '?')} -> {s['visibility_to']} at {s['scheduled_at']}")
            with sc_col2:
                if st.button("Cancel", key=f"cancel_sched_{s['id']}"):
                    delete_visibility_schedule(s["id"])
                    st.rerun()

    st.divider()

    # --- Products (each with their own discount blocks) ---
    st.subheader("Products & Discounts")
    st.caption("Add each product with its category and discount blocks.")

    products_data = st.session_state["products"]
    updated_products = []

    for p_idx, product in enumerate(products_data):
        with st.expander(f"Product {p_idx + 1}: {product.get('product_name') or '(unnamed)'}", expanded=True):
            # Product name
            prod_name = st.text_input(
                "Product Name",
                value=product.get("product_name", ""),
                key=f"prod_name_{p_idx}",
            )

            # Product category
            cat_defaults = {
                "macro": product.get("product_macro_category", ""),
                "sub": product.get("product_sub_category", ""),
                "micro": product.get("product_micro_category", ""),
            }
            cat_result = render_category_picker(f"product_{p_idx}", cat_defaults)

            # Discount blocks for this product
            st.markdown("---")
            st.markdown("**Discount Blocks**")
            product_discounts = product.get("discounts", [{}])
            updated_discs = []

            for d_idx, disc in enumerate(product_discounts):
                with st.container():
                    result = render_discount_block(p_idx, d_idx, disc)
                    updated_discs.append(result)

                    if len(product_discounts) > 1:
                        if st.button(f"Remove Discount {d_idx + 1}",
                                     key=f"remove_disc_{p_idx}_{d_idx}"):
                            product_discounts.pop(d_idx)
                            product["discounts"] = product_discounts
                            st.session_state["products"] = products_data
                            st.rerun()

            if st.button("+ Add Discount Block", key=f"add_disc_{p_idx}"):
                product_discounts.append({})
                product["discounts"] = product_discounts
                st.session_state["products"] = products_data
                st.rerun()

            updated_products.append({
                "name": prod_name,
                "macro": cat_result["macro"],
                "sub": cat_result["sub"],
                "micro": cat_result["micro"],
                "discounts": updated_discs,
            })

            # Remove product button
            if len(products_data) > 1:
                if st.button(f"Remove Product {p_idx + 1}", key=f"remove_prod_{p_idx}",
                             type="secondary"):
                    products_data.pop(p_idx)
                    st.session_state["products"] = products_data
                    st.rerun()

    if st.button("+ Add Product", type="secondary"):
        products_data.append({
            "product_name": "", "product_macro_category": "",
            "product_sub_category": "", "product_micro_category": "",
            "discounts": [{}],
        })
        st.session_state["products"] = products_data
        st.rerun()

    st.divider()

    # --- Action buttons ---
    col_save, col_delete = st.columns([3, 1])

    with col_save:
        if st.button("Save Annotation", type="primary", use_container_width=True):
            if not operator.strip():
                st.error("Please enter your operator name.")
                return
            if not updated_products:
                st.error("Please add at least one product.")
                return

            override_cat = st.session_state.get("override_brand_category", "")

            with st.spinner("Saving..."):
                save_annotation(
                    coupon_id=coupon_id,
                    operator=operator.strip(),
                    products=updated_products,
                    brand_category_override=override_cat if not detail.get("industry") else "",
                    visibility=visibility,
                )

            st.session_state["form_loaded_from_db"] = True
            st.success(f"Annotation saved for coupon {coupon_id}!")

    with col_delete:
        if st.session_state.get("form_loaded_from_db"):
            if st.button("Delete Annotation", type="secondary", use_container_width=True):
                st.session_state["confirm_delete"] = True

    # Confirmation dialog for delete
    if st.session_state.get("confirm_delete"):
        st.warning("Are you sure you want to delete this annotation?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", type="primary"):
                delete_annotation(coupon_id)
                st.session_state["form_coupon_id"] = None
                st.session_state["confirm_delete"] = False
                st.session_state["form_loaded_from_db"] = False
                st.success("Annotation deleted.")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state["confirm_delete"] = False
                st.rerun()

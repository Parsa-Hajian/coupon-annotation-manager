"""Page 2: Coupon detail view, annotation form, edit and delete."""

import streamlit as st
from bq_client import get_coupon_detail, get_existing_annotation, save_annotation, delete_annotation
from components.category_picker import render_category_picker
from components.discount_form import render_discount_block
from categories import MACRO_CATEGORIES


def _init_form_state(coupon_id: int):
    """Initialize or load form state for the selected coupon."""
    if st.session_state.get("form_coupon_id") == coupon_id:
        return

    st.session_state["form_coupon_id"] = coupon_id

    existing = get_existing_annotation(coupon_id)
    if existing:
        st.session_state["product_categories"] = existing["categories"]
        st.session_state["discount_blocks"] = existing["discounts"]
        st.session_state["form_loaded_from_db"] = True
    else:
        st.session_state["product_categories"] = [{}]
        st.session_state["discount_blocks"] = [{}]
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

    # --- Product Categories ---
    st.subheader("Product Categories")

    categories_data = st.session_state["product_categories"]
    updated_categories = []

    for i, cat in enumerate(categories_data):
        with st.container():
            cols = st.columns([10, 1])
            with cols[0]:
                defaults = {
                    "macro": cat.get("product_macro_category", ""),
                    "sub": cat.get("product_sub_category", ""),
                    "micro": cat.get("product_micro_category", ""),
                }
                result = render_category_picker(f"product_{i}", defaults)
                updated_categories.append(result)
            with cols[1]:
                if len(categories_data) > 1:
                    if st.button("X", key=f"remove_cat_{i}", help="Remove this product category"):
                        categories_data.pop(i)
                        st.session_state["product_categories"] = categories_data
                        st.rerun()

    if st.button("+ Add Product Category"):
        st.session_state["product_categories"].append({})
        st.rerun()

    st.divider()

    # --- Discount Blocks ---
    st.subheader("Discount Blocks")

    discounts_data = st.session_state["discount_blocks"]
    updated_discounts = []

    for i, disc in enumerate(discounts_data):
        with st.container():
            with st.expander(f"Discount Block {i + 1}", expanded=True):
                result = render_discount_block(i, disc)
                updated_discounts.append(result)

                if len(discounts_data) > 1:
                    if st.button(f"Remove Block {i + 1}", key=f"remove_disc_{i}"):
                        discounts_data.pop(i)
                        st.session_state["discount_blocks"] = discounts_data
                        st.rerun()

    if st.button("+ Add Discount Block"):
        st.session_state["discount_blocks"].append({})
        st.rerun()

    st.divider()

    # --- Action buttons ---
    col_save, col_delete = st.columns([3, 1])

    with col_save:
        if st.button("Save Annotation", type="primary", use_container_width=True):
            if not operator.strip():
                st.error("Please enter your operator name.")
                return
            if not updated_categories:
                st.error("Please add at least one product category.")
                return
            if not updated_discounts:
                st.error("Please add at least one discount block.")
                return

            override_cat = st.session_state.get("override_brand_category", "")

            with st.spinner("Saving..."):
                save_annotation(
                    coupon_id=coupon_id,
                    operator=operator.strip(),
                    categories=updated_categories,
                    discounts=updated_discounts,
                    brand_category_override=override_cat if not detail.get("industry") else "",
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

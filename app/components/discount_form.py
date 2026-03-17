"""Dynamic discount block form widget."""

import streamlit as st
from components.category_picker import render_category_picker

DISCOUNT_TYPES = ["Percentage", "Amount", "Payback/Cashback/Gift"]
DISCOUNT_MODIFIERS = ["Fixed", "Up to", "Starting from", "Between", "Incremental"]


def render_discount_block(index: int, defaults: dict | None = None) -> dict:
    """Render a single discount block form.

    Args:
        index: block index for unique widget keys
        defaults: optional dict for pre-population

    Returns:
        dict with all discount block fields
    """
    defaults = defaults or {}

    st.markdown(f"**Discount Block {index + 1}**")

    col1, col2 = st.columns(2)

    with col1:
        type_options = DISCOUNT_TYPES
        type_idx = 0
        if defaults.get("discount_type"):
            type_map = {"percentage": 0, "amount": 1, "payback_cashback_gift": 2}
            type_idx = type_map.get(defaults["discount_type"], 0)
        discount_type = st.selectbox(
            "Discount Type",
            type_options,
            index=type_idx,
            key=f"disc_type_{index}",
        )

    with col2:
        mod_idx = 0
        if defaults.get("discount_modifier"):
            mod_map = {"fixed": 0, "up_to": 1, "starting_from": 2, "between": 3, "incremental": 4}
            mod_idx = mod_map.get(defaults["discount_modifier"], 0)
        modifier = st.selectbox(
            "Modifier",
            DISCOUNT_MODIFIERS,
            index=mod_idx,
            key=f"disc_mod_{index}",
        )

    # Value inputs based on modifier
    value_1 = None
    value_2 = None
    values_json = ""

    if modifier == "Between":
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            value_1 = st.number_input(
                "Min Value",
                min_value=0.0,
                value=float(defaults.get("discount_value_1", 0) or 0),
                key=f"disc_v1_{index}",
            )
        with v_col2:
            value_2 = st.number_input(
                "Max Value",
                min_value=0.0,
                value=float(defaults.get("discount_value_2", 0) or 0),
                key=f"disc_v2_{index}",
            )
    elif modifier == "Incremental":
        values_str = st.text_input(
            "Values (comma-separated, e.g. 20,40,60)",
            value=defaults.get("discount_values_json", ""),
            key=f"disc_vinc_{index}",
        )
        values_json = values_str
        # Parse first value for value_1
        parts = [v.strip() for v in values_str.split(",") if v.strip()]
        if parts:
            try:
                value_1 = float(parts[0])
            except ValueError:
                pass
    else:
        # Fixed, Up to, Starting from — single value
        value_1 = st.number_input(
            "Value",
            min_value=0.0,
            value=float(defaults.get("discount_value_1", 0) or 0),
            key=f"disc_v1_{index}",
        )

    # Gift product category (only for Payback/Cashback/Gift)
    gift_is_product = False
    gift_cat = {"macro": "", "sub": "", "micro": ""}

    if discount_type == "Payback/Cashback/Gift":
        gift_is_product = st.checkbox(
            "Gift is a product?",
            value=bool(defaults.get("gift_is_product", False)),
            key=f"disc_gift_{index}",
        )
        if gift_is_product:
            st.markdown("*Gift product category:*")
            gift_defaults = {
                "macro": defaults.get("gift_macro_category", ""),
                "sub": defaults.get("gift_sub_category", ""),
                "micro": defaults.get("gift_micro_category", ""),
            }
            gift_cat = render_category_picker(f"gift_{index}", gift_defaults)

    # Map display values to storage values
    type_store_map = {
        "Percentage": "percentage",
        "Amount": "amount",
        "Payback/Cashback/Gift": "payback_cashback_gift",
    }
    mod_store_map = {
        "Fixed": "fixed",
        "Up to": "up_to",
        "Starting from": "starting_from",
        "Between": "between",
        "Incremental": "incremental",
    }

    return {
        "discount_type": type_store_map[discount_type],
        "discount_modifier": mod_store_map[modifier],
        "value_1": value_1,
        "value_2": value_2,
        "values_json": values_json,
        "gift_is_product": gift_is_product,
        "gift_macro": gift_cat["macro"] if gift_is_product else "",
        "gift_sub": gift_cat["sub"] if gift_is_product else "",
        "gift_micro": gift_cat["micro"] if gift_is_product else "",
    }

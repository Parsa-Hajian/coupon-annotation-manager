"""Reusable chained macro -> sub -> micro category selector."""

import streamlit as st
from categories import CATEGORIES, get_sub_categories, get_micro_categories, MACRO_CATEGORIES


def render_category_picker(key_prefix: str, defaults: dict | None = None) -> dict:
    """Render three chained selectboxes for category selection.

    Args:
        key_prefix: unique prefix for widget keys (e.g. "product_0" or "gift_0")
        defaults: optional dict with keys "macro", "sub", "micro" for pre-population

    Returns:
        dict with keys "macro", "sub", "micro"
    """
    defaults = defaults or {}

    col1, col2, col3 = st.columns(3)

    with col1:
        macro_idx = 0
        if defaults.get("macro") in MACRO_CATEGORIES:
            macro_idx = MACRO_CATEGORIES.index(defaults["macro"])
        macro = st.selectbox(
            "Macro Category",
            MACRO_CATEGORIES,
            index=macro_idx,
            key=f"{key_prefix}_macro",
        )

    subs = get_sub_categories(macro)
    with col2:
        sub_idx = 0
        if defaults.get("sub") in subs:
            sub_idx = subs.index(defaults["sub"])
        sub = st.selectbox(
            "Sub Category",
            subs,
            index=sub_idx,
            key=f"{key_prefix}_sub",
        )

    micros = get_micro_categories(macro, sub)
    with col3:
        micro_idx = 0
        if defaults.get("micro") in micros:
            micro_idx = micros.index(defaults["micro"])
        micro = st.selectbox(
            "Micro Category",
            micros,
            index=micro_idx,
            key=f"{key_prefix}_micro",
        )

    return {"macro": macro, "sub": sub, "micro": micro}

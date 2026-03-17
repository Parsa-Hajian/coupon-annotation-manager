"""BigQuery client for reading coupons/brands + persistent DB for annotations.

Performance strategy:
- ONE cached BQ query fetches all coupon+brand data (refreshed every 5 min).
- All filtering (time, search) happens in-memory on the cached DataFrame.
- Notification count derived from cached data — no extra BQ call.
- Coupon detail uses cached data — no extra BQ call.
- sync_status_log uses batch operations — no row-by-row loop.

Storage:
- Local dev: SQLite file (annotations.db)
- Cloud (Streamlit Cloud): Turso (libsql) — SQLite-compatible cloud DB
"""

import sqlite3
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
from google.cloud import bigquery

from config import KEY_PATH, COUPONS_TABLE, BRAND_TABLE, DB_PATH


# ---------------------------------------------------------------------------
# BigQuery client — local key file or Streamlit secrets
# ---------------------------------------------------------------------------

@st.cache_resource
def get_bq_client() -> bigquery.Client:
    if KEY_PATH:
        return bigquery.Client.from_service_account_json(KEY_PATH)
    # Streamlit Cloud: read credentials from st.secrets
    from google.oauth2 import service_account
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials)


# ---------------------------------------------------------------------------
# Database helpers — SQLite (local) or Turso (cloud)
# ---------------------------------------------------------------------------

def _use_turso() -> bool:
    """Check if Turso cloud DB is configured."""
    try:
        return bool(st.secrets.get("turso", {}).get("url"))
    except Exception:
        return False


def get_db():
    if _use_turso():
        import libsql_experimental as libsql
        url = st.secrets["turso"]["url"]
        token = st.secrets["turso"]["token"]
        conn = libsql.connect(url, auth_token=token)
        # libsql supports row_factory with sqlite3.Row
        conn.row_factory = sqlite3.Row
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


def ensure_tables_exist():
    """Create local SQLite tables for annotations on first run."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS processed_coupons (
            coupon_id INTEGER PRIMARY KEY,
            processed_by TEXT,
            processed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS product_categories (
            id TEXT PRIMARY KEY,
            coupon_id INTEGER NOT NULL,
            product_macro_category TEXT,
            product_sub_category TEXT,
            product_micro_category TEXT
        );
        CREATE TABLE IF NOT EXISTS discount_blocks (
            id TEXT PRIMARY KEY,
            coupon_id INTEGER NOT NULL,
            discount_type TEXT,
            discount_modifier TEXT,
            discount_value_1 REAL,
            discount_value_2 REAL,
            discount_values_json TEXT,
            gift_is_product INTEGER DEFAULT 0,
            gift_macro_category TEXT,
            gift_sub_category TEXT,
            gift_micro_category TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS coupon_status_log (
            coupon_id INTEGER NOT NULL,
            status TEXT,
            changed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS brand_category_overrides (
            coupon_id INTEGER PRIMARY KEY,
            brand_category TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_status_log_coupon ON coupon_status_log(coupon_id, changed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_product_cat_coupon ON product_categories(coupon_id);
        CREATE INDEX IF NOT EXISTS idx_discount_coupon ON discount_blocks(coupon_id);
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CORE: Single cached BQ fetch — all coupons + brand info
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_all_coupons_brands() -> pd.DataFrame:
    """One query to fetch all coupons joined with brands. Cached 5 min."""
    client = get_bq_client()
    query = f"""
    SELECT
        c.Id AS coupon_id,
        c.Brand AS brand_id,
        c.`Coupon Name` AS coupon_name,
        b.`Brand Name` AS brand_name,
        b.Industry AS industry,
        c.`Created Time` AS created_time,
        c.`Modified Time` AS modified_time,
        c.`Data pubblicazione` AS publish_date,
        c.`Data scadenza` AS expiry_date,
        c.`Attivo _ Non attivo` AS status,
        c.Tipologia AS tipologia,
        c.`Categoria servizi` AS categoria_servizi,
        c.`Campagna di Riferimento` AS campaign,
        c.Slug AS slug
    FROM `{COUPONS_TABLE}` c
    LEFT JOIN `{BRAND_TABLE}` b ON c.Brand = b.Id
    ORDER BY c.`Created Time` DESC
    """
    return client.query(query).to_dataframe()


def _get_processed_ids() -> set:
    """Get all processed coupon IDs from SQLite (fast local query)."""
    conn = get_db()
    rows = conn.execute("SELECT coupon_id FROM processed_coupons").fetchall()
    conn.close()
    return set(r[0] for r in rows)


# ---------------------------------------------------------------------------
# READ: filtered coupons (in-memory filtering on cached data)
# ---------------------------------------------------------------------------

def get_coupons(time_filter: str = "All", search: str = "") -> pd.DataFrame:
    """Filter cached coupon data by time period and search string."""
    df = _fetch_all_coupons_brands().copy()

    # Time filter — in-memory (use UTC-aware timestamps to match BQ data)
    if time_filter == "Today":
        cutoff = pd.Timestamp.now(tz="UTC").normalize()
        df = df[df["created_time"] >= cutoff]
    elif time_filter == "Past Week":
        cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
        df = df[df["created_time"] >= cutoff]
    elif time_filter == "Past Month":
        cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)
        df = df[df["created_time"] >= cutoff]

    # Search filter — in-memory
    if search.strip():
        s = search.strip().lower()
        mask = (
            df["coupon_name"].fillna("").str.lower().str.contains(s, na=False)
            | df["brand_name"].fillna("").str.lower().str.contains(s, na=False)
            | df["industry"].fillna("").str.lower().str.contains(s, na=False)
            | df["coupon_id"].astype(str).str.contains(s, na=False)
        )
        df = df[mask]

    # Add processing status from local SQLite
    processed_ids = _get_processed_ids()
    df["is_processed"] = df["coupon_id"].isin(processed_ids)

    return df.reset_index(drop=True)


def get_coupon_detail(coupon_id: int) -> dict | None:
    """Get a single coupon from cached data — no BQ call."""
    df = _fetch_all_coupons_brands()
    row = df[df["coupon_id"] == coupon_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def count_unprocessed_active() -> int:
    """Count active unprocessed coupons from cached data — no BQ call."""
    df = _fetch_all_coupons_brands()
    active_ids = set(df[df["status"] == "Attivo"]["coupon_id"].tolist())
    processed_ids = _get_processed_ids()
    return len(active_ids - processed_ids)


# ---------------------------------------------------------------------------
# READ: Local SQLite for existing annotations
# ---------------------------------------------------------------------------

def get_existing_annotation(coupon_id: int) -> dict | None:
    """Load existing product categories and discount blocks from SQLite."""
    conn = get_db()

    proc = conn.execute(
        "SELECT processed_by, processed_at FROM processed_coupons WHERE coupon_id = ?",
        (coupon_id,),
    ).fetchone()

    if not proc:
        conn.close()
        return None

    cats = conn.execute(
        "SELECT id, product_macro_category, product_sub_category, product_micro_category "
        "FROM product_categories WHERE coupon_id = ?",
        (coupon_id,),
    ).fetchall()

    discs = conn.execute(
        "SELECT id, discount_type, discount_modifier, discount_value_1, discount_value_2, "
        "discount_values_json, gift_is_product, gift_macro_category, gift_sub_category, "
        "gift_micro_category FROM discount_blocks WHERE coupon_id = ?",
        (coupon_id,),
    ).fetchall()

    conn.close()

    return {
        "processed_by": proc["processed_by"],
        "processed_at": proc["processed_at"],
        "categories": [dict(c) for c in cats],
        "discounts": [dict(d) for d in discs],
    }


# ---------------------------------------------------------------------------
# WRITE: Save annotations to local SQLite
# ---------------------------------------------------------------------------

def save_annotation(coupon_id: int, operator: str, categories: list[dict], discounts: list[dict],
                    brand_category_override: str = ""):
    """Save (upsert) the full annotation for a coupon to SQLite."""
    conn = get_db()
    now = datetime.utcnow().isoformat()

    conn.execute("DELETE FROM processed_coupons WHERE coupon_id = ?", (coupon_id,))
    conn.execute("DELETE FROM product_categories WHERE coupon_id = ?", (coupon_id,))
    conn.execute("DELETE FROM discount_blocks WHERE coupon_id = ?", (coupon_id,))

    # Save brand category override if provided
    if brand_category_override:
        conn.execute(
            "INSERT OR REPLACE INTO brand_category_overrides (coupon_id, brand_category) VALUES (?, ?)",
            (coupon_id, brand_category_override),
        )

    conn.execute(
        "INSERT INTO processed_coupons (coupon_id, processed_by, processed_at) VALUES (?, ?, ?)",
        (coupon_id, operator, now),
    )

    for cat in categories:
        conn.execute(
            "INSERT INTO product_categories (id, coupon_id, product_macro_category, "
            "product_sub_category, product_micro_category) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), coupon_id, cat["macro"], cat["sub"], cat["micro"]),
        )

    for disc in discounts:
        conn.execute(
            "INSERT INTO discount_blocks (id, coupon_id, discount_type, discount_modifier, "
            "discount_value_1, discount_value_2, discount_values_json, gift_is_product, "
            "gift_macro_category, gift_sub_category, gift_micro_category, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                coupon_id,
                disc["discount_type"],
                disc["discount_modifier"],
                disc.get("value_1"),
                disc.get("value_2"),
                disc.get("values_json", ""),
                1 if disc.get("gift_is_product", False) else 0,
                disc.get("gift_macro", ""),
                disc.get("gift_sub", ""),
                disc.get("gift_micro", ""),
                now,
            ),
        )

    conn.commit()
    conn.close()


def delete_annotation(coupon_id: int):
    """Remove all annotation data for a coupon from SQLite."""
    conn = get_db()
    conn.execute("DELETE FROM processed_coupons WHERE coupon_id = ?", (coupon_id,))
    conn.execute("DELETE FROM product_categories WHERE coupon_id = ?", (coupon_id,))
    conn.execute("DELETE FROM discount_blocks WHERE coupon_id = ?", (coupon_id,))
    conn.execute("DELETE FROM brand_category_overrides WHERE coupon_id = ?", (coupon_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Status tracking — BATCH optimized
# ---------------------------------------------------------------------------

def sync_status_log():
    """Batch-compare BQ statuses vs SQLite last-logged. No row-by-row loop."""
    df = _fetch_all_coupons_brands()
    if df.empty:
        return

    # Get only coupon_id + status columns
    current = df[["coupon_id", "status"]].dropna(subset=["status"]).copy()

    conn = get_db()

    # Get latest logged status per coupon in one query
    existing = conn.execute(
        "SELECT coupon_id, status FROM coupon_status_log "
        "WHERE rowid IN (SELECT MAX(rowid) FROM coupon_status_log GROUP BY coupon_id)"
    ).fetchall()
    last_status = {r["coupon_id"]: r["status"] for r in existing}

    # Find changes
    now = datetime.utcnow().isoformat()
    inserts = []
    for _, row in current.iterrows():
        cid = int(row["coupon_id"])
        s = row["status"]
        if last_status.get(cid) != s:
            inserts.append((cid, s, now))

    # Batch insert
    if inserts:
        conn.executemany(
            "INSERT INTO coupon_status_log (coupon_id, status, changed_at) VALUES (?, ?, ?)",
            inserts,
        )
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def get_all_export_data() -> pd.DataFrame:
    """Fetch ALL processed coupons with annotations — no date filter."""
    conn = get_db()
    rows = conn.execute("SELECT coupon_id, processed_by, processed_at FROM processed_coupons").fetchall()

    if not rows:
        conn.close()
        return pd.DataFrame()

    processed = {r["coupon_id"]: dict(r) for r in rows}
    coupon_ids = list(processed.keys())
    placeholders = ",".join("?" * len(coupon_ids))

    all_df = _fetch_all_coupons_brands()
    bq_df = all_df[all_df["coupon_id"].isin(coupon_ids)]

    all_cats = conn.execute(
        f"SELECT * FROM product_categories WHERE coupon_id IN ({placeholders})", coupon_ids
    ).fetchall()
    all_discs = conn.execute(
        f"SELECT * FROM discount_blocks WHERE coupon_id IN ({placeholders})", coupon_ids
    ).fetchall()
    brand_overrides_rows = conn.execute(
        f"SELECT coupon_id, brand_category FROM brand_category_overrides WHERE coupon_id IN ({placeholders})",
        coupon_ids,
    ).fetchall()
    brand_overrides = {r["coupon_id"]: r["brand_category"] for r in brand_overrides_rows}
    conn.close()

    result_rows = []
    for _, bq_row in bq_df.iterrows():
        cid = bq_row["coupon_id"]
        proc = processed.get(cid, {})
        cats = [dict(c) for c in all_cats if c["coupon_id"] == cid]
        discs = [dict(d) for d in all_discs if d["coupon_id"] == cid]

        for cat in (cats or [{}]):
            for disc in (discs or [{}]):
                result_rows.append({
                    "coupon_id": cid,
                    "brand_id": bq_row.get("brand_id"),
                    "title": bq_row["coupon_name"],
                    "brand": bq_row["brand_name"],
                    "brand_category": brand_overrides.get(cid) or bq_row["industry"],
                    "created_time": bq_row["created_time"],
                    "active_status": bq_row["status"],
                    "last_modified": bq_row["modified_time"],
                    "processed_by": proc.get("processed_by", ""),
                    "processed_at": proc.get("processed_at", ""),
                    "product_macro_category": cat.get("product_macro_category", ""),
                    "product_sub_category": cat.get("product_sub_category", ""),
                    "product_micro_category": cat.get("product_micro_category", ""),
                    "discount_type": disc.get("discount_type", ""),
                    "discount_modifier": disc.get("discount_modifier", ""),
                    "discount_value_1": disc.get("discount_value_1"),
                    "discount_value_2": disc.get("discount_value_2"),
                    "discount_values_json": disc.get("discount_values_json", ""),
                    "gift_is_product": disc.get("gift_is_product", 0),
                    "gift_macro_category": disc.get("gift_macro_category", ""),
                    "gift_sub_category": disc.get("gift_sub_category", ""),
                    "gift_micro_category": disc.get("gift_micro_category", ""),
                })

    return pd.DataFrame(result_rows)


def get_export_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch processed coupons with annotations for Excel export."""
    conn = get_db()
    rows = conn.execute(
        "SELECT coupon_id, processed_by, processed_at FROM processed_coupons "
        "WHERE processed_at >= ? AND processed_at <= ?",
        (start_date, end_date + "T23:59:59"),
    ).fetchall()

    if not rows:
        conn.close()
        return pd.DataFrame()

    processed = {r["coupon_id"]: dict(r) for r in rows}
    coupon_ids = list(processed.keys())
    placeholders = ",".join("?" * len(coupon_ids))

    # Use cached BQ data — no extra BQ call
    all_df = _fetch_all_coupons_brands()
    bq_df = all_df[all_df["coupon_id"].isin(coupon_ids)]

    # Fetch categories, discounts, and brand overrides from SQLite
    all_cats = conn.execute(
        f"SELECT * FROM product_categories WHERE coupon_id IN ({placeholders})",
        coupon_ids,
    ).fetchall()
    all_discs = conn.execute(
        f"SELECT * FROM discount_blocks WHERE coupon_id IN ({placeholders})",
        coupon_ids,
    ).fetchall()
    brand_overrides_rows = conn.execute(
        f"SELECT coupon_id, brand_category FROM brand_category_overrides WHERE coupon_id IN ({placeholders})",
        coupon_ids,
    ).fetchall()
    brand_overrides = {r["coupon_id"]: r["brand_category"] for r in brand_overrides_rows}
    conn.close()

    # Build combined dataframe
    result_rows = []
    for _, bq_row in bq_df.iterrows():
        cid = bq_row["coupon_id"]
        proc = processed.get(cid, {})
        cats = [dict(c) for c in all_cats if c["coupon_id"] == cid]
        discs = [dict(d) for d in all_discs if d["coupon_id"] == cid]

        for cat in (cats or [{}]):
            for disc in (discs or [{}]):
                result_rows.append({
                    "coupon_id": cid,
                    "brand_id": bq_row.get("brand_id"),
                    "title": bq_row["coupon_name"],
                    "brand": bq_row["brand_name"],
                    "brand_category": brand_overrides.get(cid) or bq_row["industry"],
                    "created_time": bq_row["created_time"],
                    "active_status": bq_row["status"],
                    "last_modified": bq_row["modified_time"],
                    "processed_by": proc.get("processed_by", ""),
                    "processed_at": proc.get("processed_at", ""),
                    "product_macro_category": cat.get("product_macro_category", ""),
                    "product_sub_category": cat.get("product_sub_category", ""),
                    "product_micro_category": cat.get("product_micro_category", ""),
                    "discount_type": disc.get("discount_type", ""),
                    "discount_modifier": disc.get("discount_modifier", ""),
                    "discount_value_1": disc.get("discount_value_1"),
                    "discount_value_2": disc.get("discount_value_2"),
                    "discount_values_json": disc.get("discount_values_json", ""),
                    "gift_is_product": disc.get("gift_is_product", 0),
                    "gift_macro_category": disc.get("gift_macro_category", ""),
                    "gift_sub_category": disc.get("gift_sub_category", ""),
                    "gift_micro_category": disc.get("gift_micro_category", ""),
                })

    return pd.DataFrame(result_rows)


def get_status_history(coupon_ids: list[int]) -> pd.DataFrame:
    """Fetch status change history from SQLite for given coupon IDs."""
    if not coupon_ids:
        return pd.DataFrame()
    conn = get_db()
    placeholders = ",".join("?" * len(coupon_ids))
    rows = conn.execute(
        f"SELECT coupon_id, status, changed_at FROM coupon_status_log "
        f"WHERE coupon_id IN ({placeholders}) ORDER BY coupon_id, changed_at",
        coupon_ids,
    ).fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])

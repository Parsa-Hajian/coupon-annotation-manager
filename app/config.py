import os

PROJECT_ID = "adroit-arcana-480911-k1"

_APP_DIR = os.path.dirname(os.path.abspath(__file__))

# BQ key: local file or Streamlit secrets (cloud)
_KEY_IN_APP = os.path.join(_APP_DIR, "mykey.json")
_KEY_IN_PARENT = os.path.join(_APP_DIR, "..", "mykey.json")
if os.path.exists(_KEY_IN_APP):
    KEY_PATH = _KEY_IN_APP
elif os.path.exists(_KEY_IN_PARENT):
    KEY_PATH = _KEY_IN_PARENT
else:
    KEY_PATH = None  # Will use st.secrets on Streamlit Cloud

# Existing BigQuery tables (read-only)
COUPONS_TABLE = f"{PROJECT_ID}.zoho_sync.coupons"
BRAND_TABLE = f"{PROJECT_ID}.zoho_sync.brand"

# Local SQLite database for annotations (used when Turso is not configured)
DB_PATH = os.path.join(_APP_DIR, "annotations.db")

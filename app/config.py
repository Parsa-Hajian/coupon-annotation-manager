import os

PROJECT_ID = "adroit-arcana-480911-k1"

# Look for key in app folder first, then parent folder
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_KEY_IN_APP = os.path.join(_APP_DIR, "mykey.json")
_KEY_IN_PARENT = os.path.join(_APP_DIR, "..", "mykey.json")
KEY_PATH = _KEY_IN_APP if os.path.exists(_KEY_IN_APP) else _KEY_IN_PARENT

# Existing BigQuery tables (read-only)
COUPONS_TABLE = f"{PROJECT_ID}.zoho_sync.coupons"
BRAND_TABLE = f"{PROJECT_ID}.zoho_sync.brand"

# Local SQLite database for annotations
DB_PATH = os.path.join(_APP_DIR, "annotations.db")

"""Minimal Turso HTTP client — pure Python, no native dependencies.

Provides a sqlite3-compatible interface over Turso's HTTP pipeline API.
"""

import requests


class _Row:
    """Dict-like row that supports column-name access like sqlite3.Row."""
    def __init__(self, columns, values):
        self._data = dict(zip(columns, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


class _Cursor:
    """Minimal cursor returned by execute()."""
    def __init__(self, columns, rows):
        self._columns = columns
        self._rows = [_Row(columns, r) for r in rows]
        self._iter = iter(self._rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return self._iter

    def __next__(self):
        return next(self._iter)


def _convert_arg(val):
    """Convert a Python value to Turso HTTP API arg format."""
    if val is None:
        return {"type": "null", "value": None}
    if isinstance(val, bool):
        return {"type": "integer", "value": str(int(val))}
    if isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    if isinstance(val, float):
        return {"type": "float", "value": val}
    return {"type": "text", "value": str(val)}


def _extract_value(col_val):
    """Extract a Python value from Turso HTTP API response value."""
    if col_val is None or col_val.get("type") == "null":
        return None
    t = col_val.get("type", "")
    v = col_val.get("value")
    if t == "integer":
        return int(v)
    if t == "float":
        return float(v)
    return v


class TursoConnection:
    """sqlite3.Connection-compatible wrapper for Turso HTTP API."""

    def __init__(self, url, auth_token):
        # Convert libsql:// to https://
        self._url = url.replace("libsql://", "https://") + "/v2/pipeline"
        self._token = auth_token
        self._headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self.row_factory = None  # Ignored, we always return _Row

    def _send(self, requests_list):
        """Send a pipeline request and return results."""
        body = {"requests": requests_list + [{"type": "close"}]}
        resp = requests.post(self._url, json=body, headers=self._headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def execute(self, sql, params=None):
        """Execute a single SQL statement."""
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [_convert_arg(p) for p in params]

        results = self._send([{"type": "execute", "stmt": stmt}])

        if results and results[0].get("type") == "ok":
            result = results[0]["response"]["result"]
            cols = [c["name"] for c in result.get("cols", [])]
            rows = [
                [_extract_value(v) for v in row]
                for row in result.get("rows", [])
            ]
            return _Cursor(cols, rows)

        # Check for errors
        if results and results[0].get("type") == "error":
            raise RuntimeError(results[0]["error"]["message"])

        return _Cursor([], [])

    def executemany(self, sql, params_list):
        """Execute a SQL statement with multiple parameter sets."""
        reqs = []
        for params in params_list:
            stmt = {"sql": sql, "args": [_convert_arg(p) for p in params]}
            reqs.append({"type": "execute", "stmt": stmt})
        if reqs:
            self._send(reqs)

    def executescript(self, script):
        """Execute multiple SQL statements separated by semicolons."""
        statements = [s.strip() for s in script.split(";") if s.strip()]
        reqs = [{"type": "execute", "stmt": {"sql": s}} for s in statements]
        if reqs:
            self._send(reqs)

    def commit(self):
        """No-op — Turso auto-commits."""
        pass

    def close(self):
        """No-op — HTTP is stateless."""
        pass

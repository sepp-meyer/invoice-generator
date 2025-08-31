import urllib.parse
import requests
from urllib.parse import urlparse
from flask import current_app
from .token_store import resolve_token, resolve_service_base

def _bridge_url(entry_id: str, base: str) -> str:
    base = base.rstrip("/")
    eid = urllib.parse.quote(entry_id, safe="")
    return f"{base}/bridge/entry/{eid}"

def fetch_entry(entry_id: str) -> dict:
    base = resolve_service_base(current_app.config["SERVICE_BASE"])
    timeout = current_app.config["REQUEST_TIMEOUT"]
    token = resolve_token()

    if not token:
        raise PermissionError("No API token configured. Please set a Bearer token in Settings.")

    url = _bridge_url(entry_id, base)

    # HARTE HTTPS-REGEL (außer echte Local-Entwicklung)
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" and host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Refusing to call non-HTTPS bridge endpoint. Please use an https:// base URL.")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        # WICHTIG: Redirects NICHT folgen, damit nie ein Token via HTTP rausgeht
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=False)
    except Exception as e:
        raise RuntimeError(f"Bridge request failed: {e}") from e

    # Falls der Server doch redirecten will: abbrechen
    if 300 <= r.status_code < 400:
        loc = r.headers.get("Location", "")
        raise RuntimeError(f"Bridge attempted to redirect to {loc!r}; refusing redirect for security.")

    if r.status_code == 401:
        raise PermissionError("Unauthorized (401). Check token or token scope.")
    if r.status_code == 403:
        raise PermissionError("Forbidden (403). Token lacks required permissions.")
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} from bridge endpoint.")

    try:
        return r.json()
    except Exception:
        raise RuntimeError("Non-JSON response from bridge endpoint.")

import urllib.parse
import requests
from flask import current_app, session, has_request_context
from .token_store import resolve_token, resolve_service_base

def _candidate_urls(entry_id: str, base: str):
    base = base.rstrip("/")
    eid = urllib.parse.quote(entry_id, safe="")
    return [
        f"{base}/bridge/entry/{eid}",
        f"{base}/api/entries/{eid}",
        f"{base}/entries/{eid}?format=json",
    ]

def fetch_entry(entry_id: str) -> dict:
    timeout = current_app.config["REQUEST_TIMEOUT"]
    base = resolve_service_base(current_app.config["SERVICE_BASE"])
    token = resolve_token()

    headers_base = {"Accept": "application/json"}
    if token:
        # Bridge erwartet den Token im Header:
        headers_base["X-Bridge-Token"] = token

    last_err = None
    for url in _candidate_urls(entry_id, base):
        try:
            r = requests.get(url, headers=headers_base, timeout=timeout)
            if r.ok:
                try:
                    return r.json()
                except Exception:
                    last_err = RuntimeError(f"Non-JSON response @ {url}")
                    continue
            else:
                last_err = RuntimeError(f"HTTP {r.status_code} @ {url}")
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("No endpoint worked")

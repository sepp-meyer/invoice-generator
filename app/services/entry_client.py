from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Tuple
import requests
from flask import current_app

# ---------------- HTTP-Fetch mit Fallbacks ----------------

def _build_candidate_urls(entry_id: str) -> List[str]:
    base = current_app.config["ENTRY_HOST"].rstrip("/") + current_app.config["SPACE_PREFIX"]
    return [
        f"{base}/bridge/entry/{entry_id}",
        f"{base}/api/entries/{entry_id}",
        f"{base}/entries/{entry_id}?format=json",
    ]

def fetch_entry(entry_id: str) -> Tuple[Dict[str, Any], str]:
    headers = {"Accept": "application/json"}
    bearer = current_app.config.get("ENTRY_API_BEARER")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    timeout = current_app.config.get("HTTP_TIMEOUT", 10.0)
    last_err = None

    for url in _build_candidate_urls(entry_id):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code >= 400:
                last_err = RuntimeError(f"HTTP {r.status_code} @ {url}")
                continue

            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                return r.json(), url

            try:
                return json.loads(r.text), url
            except Exception:
                last_err = RuntimeError(f"Nicht-JSON Antwort @ {url}")
                continue
        except Exception as e:
            last_err = e
            continue

    raise last_err or RuntimeError("Kein passender Endpunkt lieferte eine gültige Antwort.")

# ---------------- Meta-Helpers ----------------

def _norm(s: str) -> str:
    return s.lower().replace("-", "").replace("_", "").strip()

def first_meta(meta: Dict[str, Any], candidates: List[str]) -> Optional[Any]:
    lookup = {_norm(k): k for k in meta.keys()}
    for cand in candidates:
        k_norm = _norm(cand)
        if k_norm in lookup:
            raw = meta[lookup[k_norm]]
            if isinstance(raw, list):
                return raw[0] if raw else None
            return raw
    return None

def find_meta_block(bundle: Dict[str, Any]) -> Dict[str, Any]:
    meta = (bundle.get("specific") or {}).get("meta")
    if isinstance(meta, dict):
        return meta
    meta = bundle.get("meta")
    if isinstance(meta, dict):
        return meta
    return {}

def extract_minimal_fields(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Rechnungs-Nr": first_meta(meta, ["Rechnungs-Nr", "rechnungs-nr", "invoice_no", "invoice-number"]),
        "Stadt":         first_meta(meta, ["Stadt", "city"]),
        "Datum":         first_meta(meta, ["date", "Datum", "issue_date"]),
        "Betreff":       first_meta(meta, ["Betreff", "subject"]),
        "Item":          first_meta(meta, ["Item", "item"]),
        "Quantity":      first_meta(meta, ["Quantity", "quantity"]),
        "Net_Amount":    first_meta(meta, ["Net_Amount", "net_amount", "net", "netto"]),
        "VAT":           first_meta(meta, ["VAT", "vat"]),
        "Gross_Amount":  first_meta(meta, ["Gross_Amount", "gross_amount", "gross", "brutto"]),
        "Total":         first_meta(meta, ["Total", "total"]),
        "service_Text":  first_meta(meta, ["service_Text", "service_text"]),
        "Production":    first_meta(meta, ["Production", "production"]),
        "Phase":         first_meta(meta, ["Phase", "phase"]),
        "Period":        first_meta(meta, ["Period", "period"]),
        "Extension":     first_meta(meta, ["Extension", "extension"]),
    }

# ---------------- Pfad-Analyse ----------------

def _type_path(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    return ((bundle.get("general") or {}).get("type_path") or [])

def find_parent_id_for_type(bundle: Dict[str, Any], wanted_type: str) -> Optional[str]:
    """
    Nimmt general.type_path (Liste von {'id','type'}) und liefert die letzte ID,
    deren type == wanted_type (case-insensitive).
    """
    target_id = None
    for node in _type_path(bundle):
        t = (node.get("type") or "").strip().lower()
        if t == (wanted_type or "").strip().lower():
            target_id = node.get("id")
    return target_id

def find_parents(bundle: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Praktischer Wrapper, liefert IDs für zentrale Parent-Knoten.
    """
    return {
        "firma_id":      find_parent_id_for_type(bundle, "Firma"),
        "production_id": find_parent_id_for_type(bundle, "Production"),
        "phase_id":      find_parent_id_for_type(bundle, "Phase"),
    }

# ---------------- General-Summary (Text-Ansicht) ----------------

def extract_general_summary(bundle: Dict[str, Any]) -> Dict[str, Any]:
    gen = bundle.get("general") or {}
    return {
        "id": gen.get("id"),
        "type": gen.get("type"),
        "title": gen.get("title"),
        "tags": gen.get("tags") or [],
        "created_at": gen.get("created_at"),
        "parent_id": gen.get("parent_id"),
        "path": gen.get("path"),
    }

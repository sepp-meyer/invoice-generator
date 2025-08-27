from __future__ import annotations
from flask import Blueprint, current_app, render_template, request
from ..services.entry_client import (
    fetch_entry,
    find_meta_block,
    extract_minimal_fields,
    extract_general_summary,
    find_parents,
)
import json

bp = Blueprint("main", __name__)

@bp.get("/healthz")
def healthz():
    return {
        "ok": True,
        "entry_host": current_app.config["ENTRY_HOST"],
        "space_prefix": current_app.config["SPACE_PREFIX"],
    }

@bp.route("/", methods=["GET", "POST"])
def index():
    entry_id = (request.form.get("entry_id") or "").strip()
    action   = (request.form.get("action") or "").strip()

    ctx = {
        # Eingaben
        "entry_id": entry_id,
        "action": action,

        # Invoice
        "invoice_used_url": "",
        "invoice_general": None,
        "invoice_minimal": None,
        "invoice_bundle_raw": "",
        "invoice_meta_raw": "",
        "firma_id": "",
        "production_id": "",

        # Firma
        "firma_used_url": "",
        "firma_general": None,
        "firma_meta_raw": "",

        # Production
        "production_used_url": "",
        "production_general": None,
        "production_meta_raw": "",

        # Fehler
        "error": "",
    }

    # GET → Formular leer anzeigen
    if request.method == "GET":
        return render_template("index.html", **ctx)

    # POST → je nach Action
    try:
        if action in ("", "fetch_invoice"):
            # 1) Rechnung abrufen
            if not entry_id:
                raise RuntimeError("Bitte eine Rechnungs-ID eingeben.")

            inv_bundle, inv_url = fetch_entry(entry_id)
            inv_meta = find_meta_block(inv_bundle)

            ctx["invoice_used_url"] = inv_url
            ctx["invoice_general"] = extract_general_summary(inv_bundle)
            ctx["invoice_minimal"] = extract_minimal_fields(inv_meta)
            ctx["invoice_bundle_raw"] = json.dumps(inv_bundle, indent=2, ensure_ascii=False)
            ctx["invoice_meta_raw"] = json.dumps(inv_meta, indent=2, ensure_ascii=False)

            # Parent-IDs ermitteln
            parents = find_parents(inv_bundle)
            ctx["firma_id"] = parents.get("firma_id") or ""
            ctx["production_id"] = parents.get("production_id") or ""

        elif action == "fetch_firma":
            # 2) Firma abrufen (per verstecktem Feld)
            firma_id = (request.form.get("firma_id") or "").strip()
            if not firma_id:
                raise RuntimeError("Keine Firma-ID gefunden. Bitte zuerst Rechnung abrufen.")
            firm_bundle, firm_url = fetch_entry(firma_id)
            firm_meta = find_meta_block(firm_bundle)

            ctx["firma_used_url"] = firm_url
            ctx["firma_general"] = extract_general_summary(firm_bundle)
            ctx["firma_meta_raw"] = json.dumps(firm_meta, indent=2, ensure_ascii=False)

            # damit die Buttons sichtbar bleiben, reichen wir IDs wieder durch
            ctx["entry_id"] = (request.form.get("entry_id") or "").strip()
            ctx["firma_id"] = firma_id
            ctx["production_id"] = (request.form.get("production_id") or "").strip()

        elif action == "fetch_production":
            # 3) Production abrufen
            production_id = (request.form.get("production_id") or "").strip()
            if not production_id:
                raise RuntimeError("Keine Production-ID gefunden. Bitte zuerst Rechnung abrufen.")
            prod_bundle, prod_url = fetch_entry(production_id)
            prod_meta = find_meta_block(prod_bundle)

            ctx["production_used_url"] = prod_url
            ctx["production_general"] = extract_general_summary(prod_bundle)
            ctx["production_meta_raw"] = json.dumps(prod_meta, indent=2, ensure_ascii=False)

            # IDs zurückreichen
            ctx["entry_id"] = (request.form.get("entry_id") or "").strip()
            ctx["firma_id"] = (request.form.get("firma_id") or "").strip()
            ctx["production_id"] = production_id

        else:
            raise RuntimeError(f"Unbekannte Aktion: {action}")

    except Exception as e:
        ctx["error"] = str(e)

    return render_template("index.html", **ctx)

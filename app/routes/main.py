from __future__ import annotations
from flask import Blueprint, current_app, render_template, request
from ..services.entry_client import fetch_entry, find_meta_block, extract_minimal_fields
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
    ctx = {
        "entry_id": entry_id,
        "used_url": "",
        "error": "",
        "minimal": None,
        "meta_raw": "",
        "bundle_raw": "",
    }

    if request.method == "POST":
        if not entry_id:
            ctx["error"] = "Bitte eine Entry-ID eingeben."
            return render_template("index.html", **ctx)

        try:
            bundle, used_url = fetch_entry(entry_id)
            meta = find_meta_block(bundle)
            minimal = extract_minimal_fields(meta)

            ctx.update(
                used_url=used_url,
                minimal=minimal,
                meta_raw=json.dumps(meta, indent=2, ensure_ascii=False),
                bundle_raw=json.dumps(bundle, indent=2, ensure_ascii=False),
            )
        except Exception as e:
            ctx["error"] = str(e)

    return render_template("index.html", **ctx)

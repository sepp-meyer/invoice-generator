from flask import Blueprint, render_template, jsonify, session
from ..services.entry_api import fetch_entry

bp = Blueprint("main", __name__)

def ensure_ctx():
    session.setdefault("ctx", {
        "invoice_id": None,
        "company_id": None,
        "production_id": None,
        "customer_id": None,
    })
    return session["ctx"]

@bp.get("/")
def index():
    ensure_ctx()
    return render_template("index.html")

@bp.get("/api/entry/<entry_id>")
def api_entry(entry_id):
    try:
        data = fetch_entry(entry_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

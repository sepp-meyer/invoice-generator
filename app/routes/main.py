from flask import render_template, request, jsonify, session, current_app, redirect, url_for
from . import bp
from app.services.entry_api import fetch_entry
from app.utils.formatting import (
    meta_first, euro2, format_english_date,
    derive_company_id_from_invoice, derive_prod_id_from_invoice,
    derive_customer_id_from_prod
)

# -------- Index --------
@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# -------- JSON helper endpoints (wie bisher) --------
@bp.get("/api/entry/<entry_id>")
def api_entry(entry_id):
    try:
        data = fetch_entry(entry_id)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# -------- Render final invoice (new tab) --------
@bp.get("/render_invoice")
def render_invoice():
    """
    Erzeugt die fertige, eigenständige HTML-Rechnung.
    Erwartet: invoice_id (Pflicht), optional company_id, prod_id, customer_id.
    Fehlende IDs werden – soweit möglich – aus den Datensätzen hergeleitet.
    """
    invoice_id  = (request.args.get("invoice_id") or "").strip()
    company_id  = (request.args.get("company_id") or "").strip()
    prod_id     = (request.args.get("prod_id") or "").strip()
    customer_id = (request.args.get("customer_id") or "").strip()

    if not invoice_id:
        return "Missing invoice_id", 400

    # 1) Rechnung
    invoice = fetch_entry(invoice_id)

    # 2) Firma/Production ableiten, falls nicht mitgegeben
    if not company_id:
        company_id = derive_company_id_from_invoice(invoice) or ""
    if not prod_id:
        prod_id = derive_prod_id_from_invoice(invoice) or ""

    company = fetch_entry(company_id) if company_id else None
    prod    = fetch_entry(prod_id) if prod_id else None

    # 3) Kunde ableiten (aus Production.references_to) falls nicht mitgegeben
    if not customer_id and prod:
        customer_id = derive_customer_id_from_prod(prod) or ""
    customer = fetch_entry(customer_id) if customer_id else None

    # 4) Daten für Template mappen
    # --- Firma ---
    firm_title  = (company or {}).get("general", {}).get("title", "") or "—"
    firm_name   = meta_first(company, "Adresse_1", "")
    firm_street = meta_first(company, "Adresse_2", "")
    firm_city   = meta_first(company, "Adresse_3", "")
    firm_role   = meta_first(company, "Firma_text", "")
    firm_mail   = meta_first(company, "Email", "")
    firm_phone  = meta_first(company, "Telefon", "")
    firm_taxid  = meta_first(company, "Tax-ID", "")

    # --- Kunde ---
    cust_title  = (customer or {}).get("general", {}).get("title", "") or ""
    cust_line1  = meta_first(customer, "Adresse_1", "")
    cust_line2  = meta_first(customer, "Adresse_2", "")
    cust_line3  = meta_first(customer, "Adresse_3", "")

    # --- Rechnungsspezifisch ---
    inv_no      = meta_first(invoice, "Rechnungs-Nr", "")
    city        = meta_first(invoice, "Stadt", "")
    date_raw    = meta_first(invoice, "date", "")
    date_nice   = format_english_date(date_raw) if date_raw else ""
    subject     = meta_first(invoice, "Betreff", "")
    production  = meta_first(invoice, "Production", "")
    phase       = meta_first(invoice, "Phase", "")
    period      = meta_first(invoice, "Period", "")
    extension   = meta_first(invoice, "Extension", "")
    item        = meta_first(invoice, "Item", "")
    qty         = meta_first(invoice, "Quantity", "")
    net_amt     = euro2(meta_first(invoice, "Net_Amount", ""))
    vat         = meta_first(invoice, "VAT", "")
    gross_amt   = euro2(meta_first(invoice, "Gross_Amount", ""))
    total       = euro2(meta_first(invoice, "Total", ""))
    service_txt = meta_first(invoice, "service_Text", "")

    # 5) Template rendern (exakt deiner Vorlage nachempfunden)
    return render_template(
        "invoice.html",
        firm_title=firm_title,
        firm_header_text=firm_title.lower(),  # "sepp-meyer"
        firm_name=firm_name,
        firm_role=firm_role,
        firm_street=firm_street,
        firm_city=firm_city,
        firm_mail=firm_mail,
        firm_phone=firm_phone,
        firm_taxid=firm_taxid,

        cust_title=cust_title,
        cust_line1=cust_line1,
        cust_line2=cust_line2,
        cust_line3=cust_line3,

        inv_no=inv_no,
        city=city,
        date_nice=date_nice,
        subject=subject,

        production=production,
        phase=phase,
        period=period,
        extension=extension,

        item=item,
        qty=qty,
        net_amt=net_amt,
        vat=vat,
        gross_amt=gross_amt,
        total=total,
        service_txt=service_txt,

        # Bankdaten – aktuell leer; später aus Firma/anderem Entry füllen
        bank=None
    )

from flask import render_template, request, jsonify, session, current_app, redirect, url_for
from . import bp
from app.services.entry_api import fetch_entry
from app.services.token_store import (
    resolve_token, resolve_service_base, write_persisted_token, read_persisted_token, coerce_https
)
from app.utils.formatting import (
    meta_first, euro2, format_english_date,
    derive_company_id_from_invoice, derive_prod_id_from_invoice,
    derive_customer_id_from_prod, format_iban_html
)

# -------- Index / Settings --------
@bp.route("/", methods=["GET"])
def index():
    base_eff = resolve_service_base(current_app.config["SERVICE_BASE"])
    tok_eff = resolve_token() or ""
    tok_mask = (tok_eff[:4] + "…" + tok_eff[-4:]) if len(tok_eff) >= 10 else (tok_eff or "—")
    persisted = True if (read_persisted_token() or "") else False
    return render_template("index.html",
                           service_base_value=base_eff,
                           token_mask=tok_mask,
                           has_persisted=persisted)

@bp.post("/settings")
def save_settings():
    # Service-Base (gleich beim Speichern auf https „biegen“, außer localhost)
    base_raw = (request.form.get("service_base") or "").strip()
    base = coerce_https(base_raw)
    base = base.rstrip("/")
    if base:
        session["service_base"] = base
    else:
        session.pop("service_base", None)

    # API Token (Bearer)
    token = (request.form.get("api_token") or "").strip()
    remember = bool(request.form.get("remember"))

    if token:
        session["api_token"] = token
        session.pop("bridge_token", None)
        if remember:
            write_persisted_token(token)
        else:
            write_persisted_token(None)
    else:
        session.pop("api_token", None)
        if remember:
            write_persisted_token(None)

    return redirect(url_for("main.index", saved="1"))

# -------- JSON helper endpoints --------
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
    invoice_id  = (request.args.get("invoice_id") or "").strip()
    company_id  = (request.args.get("company_id") or "").strip()
    prod_id     = (request.args.get("prod_id") or "").strip()
    customer_id = (request.args.get("customer_id") or "").strip()

    if not invoice_id:
        return render_template(
            "error.html",
            title="Fehlende Parameter",
            headline="Fehlende Parameter",
            message="Es fehlt die Rechnungs-ID.",
            status_code=400
        ), 400

    # Vor dem ersten Call: existiert überhaupt ein Token?
    if not resolve_token():
        return render_template(
            "error.html",
            title="Kein Token gesetzt",
            headline="Nicht autorisiert",
            message="Es ist kein API-Token hinterlegt.",
            status_code=401,
            tips=[
                "Öffne die Einstellungen und trage einen gültigen Token ein.",
                "Falls der Token in EntryFrame abgelaufen ist: neuen Token erzeugen und hier eintragen."
            ],
        ), 401

    # 1) Rechnung laden (mit sauberem Fehlerbild)
    try:
        invoice = fetch_entry(invoice_id)
    except PermissionError as e:
        return render_template(
            "error.html",
            title="Nicht autorisiert",
            headline="Nicht autorisiert (401)",
            message=str(e),
            status_code=401,
            tips=[
                "Token prüfen (Tipp: in Einstellungen neu speichern).",
                "In EntryFrame Admin ggf. Token reaktivieren oder neu generieren.",
            ],
        ), 401
    except Exception as e:
        return render_template(
            "error.html",
            title="Abruf fehlgeschlagen",
            headline="Rechnung konnte nicht geladen werden",
            message=f"{e}",
            status_code=400
        ), 400

    # 2) Firma/Production ableiten
    if not company_id:
        company_id = derive_company_id_from_invoice(invoice) or ""
    if not prod_id:
        prod_id = derive_prod_id_from_invoice(invoice) or ""

    def _safe_fetch(label, eid):
        if not eid:
            return None, None
        try:
            return fetch_entry(eid), None
        except PermissionError as e:
            return None, render_template(
                "error.html",
                title="Nicht autorisiert",
                headline="Nicht autorisiert (401)",
                message=f"{label} ({eid}) konnte nicht geladen werden: {e}",
                status_code=401,
                tips=[
                    "Token prüfen/erneuern und erneut versuchen.",
                    "Stimmt der Zugriffsumfang (Scope) dieses Tokens?"
                ],
            ), 401
        except Exception as e:
            return None, render_template(
                "error.html",
                title="Abruf fehlgeschlagen",
                headline=f"{label} konnte nicht geladen werden",
                message=f"{e}",
                status_code=400
            ), 400

    company, err = _safe_fetch("Firma", company_id)
    if err: return err
    prod, err = _safe_fetch("Production", prod_id)
    if err: return err

    # 3) Kunde ableiten
    customer_id = customer_id or (derive_customer_id_from_prod(prod) if prod else "") or ""
    customer, err = _safe_fetch("Kunde", customer_id)
    if err: return err

    # ---- Map Daten ---- (unverändert)
    firm_title  = (company or {}).get("general", {}).get("title", "") or "—"
    firm_name   = meta_first(company, "Adresse_1", "")
    firm_street = meta_first(company, "Adresse_2", "")
    firm_city   = meta_first(company, "Adresse_3", "")
    firm_role   = meta_first(company, "Firma_text", "")
    firm_mail   = meta_first(company, "Email", "")
    firm_phone  = meta_first(company, "Telefon", "")
    firm_taxid  = meta_first(company, "Tax-ID", "")

    cust_title  = (customer or {}).get("general", {}).get("title", "") or ""
    cust_line1  = meta_first(customer, "Adresse_1", "")
    cust_line2  = meta_first(customer, "Adresse_2", "")
    cust_line3  = meta_first(customer, "Adresse_3", "")

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

    bank = None
    if company:
        bank_name = meta_first(company, "Bank", "")
        iban_raw  = meta_first(company, "IBAN", "")
        bic       = meta_first(company, "BIC", "")
        holder    = firm_name
        if bank_name or iban_raw or bic or holder:
            bank = {
                "holder": holder,
                "bank": bank_name,
                "iban_html": format_iban_html(iban_raw) if iban_raw else "",
                "bic": bic,
            }

    return render_template(
        "invoice.html",
        firm_title=firm_title,
        firm_header_text=firm_title.lower(),
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

        bank=bank
    )

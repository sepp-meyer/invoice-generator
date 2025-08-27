from datetime import datetime

MONTHS_EN = [
    None, "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def ordinal_en(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def format_english_date(yyyymmdd: str) -> str:
    try:
        d = datetime.strptime(yyyymmdd, "%Y-%m-%d")
        return f"{MONTHS_EN[d.month]} {ordinal_en(d.day)}, {d.year}"
    except Exception:
        return yyyymmdd

def meta_first(entry: dict, key: str, default: str = "") -> str:
    try:
        meta = entry.get("specific", {}).get("meta", {})
        arr = meta.get(key, [])
        return arr[0] if arr else default
    except Exception:
        return default

def euro2(value) -> str:
    try:
        return f"{float(value):.2f}"
    except Exception:
        try:
            return f"{float(str(value).replace(',', '.')):.2f}"
        except Exception:
            return str(value)

def format_iban_html(iban: str) -> str:
    """
    Formatiert eine IBAN in 4er-Gruppen mit &nbsp; (non-breaking):
    'DE48500105175412821655' -> 'DE48&nbsp;5001&nbsp;0517&nbsp;5412&nbsp;8216&nbsp;55'
    Nimmt auch bereits gruppierte Eingaben entgegen.
    """
    raw = "".join(str(iban).split())
    if not raw:
        return ""
    groups = [raw[i:i+4] for i in range(0, len(raw), 4)]
    return "&nbsp;".join(groups)

def derive_company_id_from_invoice(inv: dict) -> str | None:
    p = inv.get("general", {}).get("path", "")
    parts = p.split(".")
    return parts[0] if len(parts) >= 1 and parts[0] else None

def derive_prod_id_from_invoice(inv: dict) -> str | None:
    p = inv.get("general", {}).get("path", "")
    parts = p.split(".")
    return parts[1] if len(parts) >= 2 and parts[1] else None

def derive_customer_id_from_prod(prod: dict) -> str | None:
    for ref in prod.get("references_to", []):
        if ref.get("dst_type") == "Kunde":
            return ref.get("dst_id")
    return None

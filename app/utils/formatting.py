from datetime import datetime

MONTHS_EN = [
    None, "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def ordinal_en(n: int) -> str:
    # 1->1st, 2->2nd, 3->3rd, 4->4th ...
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def format_english_date(yyyymmdd: str) -> str:
    # "2025-08-01" -> "August 1st, 2025"
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
    # "600" -> "600.00"
    try:
        return f"{float(value):.2f}"
    except Exception:
        try:
            return f"{float(str(value).replace(',', '.')):.2f}"
        except Exception:
            return str(value)

def derive_company_id_from_invoice(inv: dict) -> str | None:
    # path like "sE68dmVD.5XxZlp0J.7ZZRRPBT.dch6FvUW" -> first is company
    p = inv.get("general", {}).get("path", "")
    parts = p.split(".")
    return parts[0] if len(parts) >= 1 and parts[0] else None

def derive_prod_id_from_invoice(inv: dict) -> str | None:
    p = inv.get("general", {}).get("path", "")
    parts = p.split(".")
    return parts[1] if len(parts) >= 2 and parts[1] else None

def derive_customer_id_from_prod(prod: dict) -> str | None:
    # search production.references_to for dst_type == "Kunde"
    for ref in prod.get("references_to", []):
        if ref.get("dst_type") == "Kunde":
            return ref.get("dst_id")
    return None
